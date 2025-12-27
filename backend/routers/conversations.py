from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import List
import uuid
import json
import asyncio
from .. import storage, auth
from ..schemas import CreateConversationRequest, SendMessageRequest, ConversationMetadata, Conversation
from ..council import (
    run_full_council, 
    generate_conversation_title, 
    stage1_collect_responses, 
    stage2_collect_rankings, 
    stage3_synthesize_final, 
    calculate_aggregate_rankings
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationMetadata])
async def list_conversations(current_user: dict = Depends(auth.get_current_user)):
    """List all conversations (metadata only)."""
    return storage.list_conversations(current_user["username"])


@router.post("", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest, current_user: dict = Depends(auth.get_current_user)):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id, current_user["username"])
    return conversation


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str, current_user: dict = Depends(auth.get_current_user)):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Check ownership
    if conversation.get("user_id") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this conversation")
        
    return conversation


@router.post("/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest, current_user: dict = Depends(auth.get_current_user)):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Check ownership
    if conversation.get("user_id") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    # Fetch user preferences
    user_data = storage.get_user(current_user["username"])
    council_models = user_data.get("council_models")
    chairman_model = user_data.get("chairman_model")
    api_key = user_data.get("openrouter_api_key")

    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        council_models=council_models,
        chairman_model=chairman_model,
        api_key=api_key
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@router.post("/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest, current_user: dict = Depends(auth.get_current_user)):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Check ownership
    if conversation.get("user_id") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Fetch user preferences
            user_data = storage.get_user(current_user["username"])
            council_models = user_data.get("council_models")
            chairman_model = user_data.get("chairman_model")
            api_key = user_data.get("openrouter_api_key")

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content, api_key=api_key))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content, council_models=council_models, api_key=api_key)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results, council_models=council_models, api_key=api_key)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results, chairman_model=chairman_model, api_key=api_key)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(auth.get_current_user)):
    """Delete a conversation permanently."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Check ownership
    if conversation.get("user_id") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
        
    storage.delete_conversation(conversation_id)
    return {"message": "Conversation deleted successfully"}
