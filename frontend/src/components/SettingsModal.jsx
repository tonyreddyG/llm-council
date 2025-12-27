import { useState, useEffect } from 'react';
import { api } from '../api';
import './ProfileModal.css'; // Reuse styles

export default function SettingsModal({ onClose }) {
    const [activeTab, setActiveTab] = useState('models');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);

    // Model Settings
    const [availableModels, setAvailableModels] = useState([]);
    const [councilModels, setCouncilModels] = useState([]);
    const [chairmanModel, setChairmanModel] = useState('');
    const [showFreeOnly, setShowFreeOnly] = useState(false); // Changed to false by default
    const [modelSearch, setModelSearch] = useState('');

    // API Key
    const [apiKey, setApiKey] = useState('');
    const [hasApiKey, setHasApiKey] = useState(false);
    const [maskedApiKey, setMaskedApiKey] = useState('');

    useEffect(() => {
        if (activeTab === 'models' || activeTab === 'apikey') {
            fetchPreferences();
        }
        if (activeTab === 'models' && availableModels.length === 0) {
            fetchModels();
        }
    }, [activeTab]);

    const fetchModels = async () => {
        setLoading(true);
        setError(null);
        try {
            console.log('Fetching models from API...');
            const resp = await api.getAvailableModels();
            console.log('API response:', resp);

            if (!resp || !resp.data) {
                console.error('Invalid response format:', resp);
                setError("Invalid response from server. Please try again.");
                setLoading(false);
                return;
            }

            const models = resp.data || [];
            console.log(`Received ${models.length} models`);

            // Sort by name
            const sortedModels = models.sort((a, b) => {
                const nameA = a.name || '';
                const nameB = b.name || '';
                return nameA.localeCompare(nameB);
            });

            setAvailableModels(sortedModels);
        } catch (err) {
            console.error("Error fetching models:", err);
            setError(`Failed to load models: ${err.message || 'Unknown error'}. Check browser console for details.`);
        } finally {
            setLoading(false);
        }
    };

    const fetchPreferences = async () => {
        try {
            const prefs = await api.getUserPreferences();
            setCouncilModels(prefs.council_models || []);
            setChairmanModel(prefs.chairman_model || '');
            setHasApiKey(prefs.has_api_key || false);
            setMaskedApiKey(prefs.masked_api_key || '');
        } catch (err) {
            console.error("Error fetching preferences:", err);
        }
    };

    const handleSaveModels = async () => {
        if (councilModels.length < 2 || councilModels.length > 5) {
            setError("Please select 2-5 council models");
            return;
        }
        if (!chairmanModel) {
            setError("Please select a chairman model");
            return;
        }

        setLoading(true);
        setError(null);
        setMessage(null);

        try {
            await api.updateUserPreferences({
                council_models: councilModels,
                chairman_model: chairmanModel
            });
            setMessage("Model preferences saved successfully!");
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveApiKey = async (e) => {
        e.preventDefault();
        if (!apiKey.trim()) {
            setError("Please enter an API key");
            return;
        }

        setLoading(true);
        setError(null);
        setMessage(null);

        try {
            await api.updateUserPreferences({ openrouter_api_key: apiKey });
            setMessage("API Key saved successfully!");
            setHasApiKey(true);
            setApiKey('');
            await fetchPreferences();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleClearApiKey = async () => {
        if (!window.confirm("Remove your custom API key? The system will fall back to the default key.")) {
            return;
        }

        setLoading(true);
        setError(null);
        setMessage(null);

        try {
            await api.updateUserPreferences({ openrouter_api_key: "" });
            setMessage("API Key cleared. Using system default.");
            setHasApiKey(false);
            setMaskedApiKey('');
            await fetchPreferences();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const filteredModels = availableModels.filter(m => {
        // Check if model is free using optional chaining
        const isFree = m.pricing?.input === '0' && m.pricing?.output === '0';
        if (showFreeOnly && !isFree) return false;
        if (modelSearch && !m.name.toLowerCase().includes(modelSearch.toLowerCase())) return false;
        return true;
    });

    const toggleCouncilModel = (modelId) => {
        setCouncilModels(prev => {
            if (prev.includes(modelId)) {
                return prev.filter(id => id !== modelId);
            } else {
                if (prev.length >= 5) return prev;
                return [...prev, modelId];
            }
        });
    };

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setMessage(null);
        setError(null);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content settings-modal">
                <div className="modal-header">
                    <h2>Settings</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="modal-tabs">
                    <button className={`tab-btn ${activeTab === 'models' ? 'active' : ''}`} onClick={() => handleTabChange('models')}>
                        AI Models
                    </button>
                    <button className={`tab-btn ${activeTab === 'apikey' ? 'active' : ''}`} onClick={() => handleTabChange('apikey')}>
                        API Key
                    </button>
                </div>

                <div className="modal-body">
                    {message && <div className="success-message">{message}</div>}
                    {error && <div className="error-message">{error}</div>}

                    {activeTab === 'models' && (
                        <div className="models-tab">
                            <div className="filter-bar">
                                <label className="toggle-label">
                                    <input type="checkbox" checked={showFreeOnly} onChange={(e) => setShowFreeOnly(e.target.checked)} />
                                    Show Free Models Only
                                </label>
                                <input
                                    type="text"
                                    placeholder="Search models..."
                                    value={modelSearch}
                                    onChange={(e) => setModelSearch(e.target.value)}
                                    className="search-input"
                                />
                            </div>

                            <div className="openrouter-link">
                                <a href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer">
                                    View all models on OpenRouter →
                                </a>
                            </div>

                            <div className="models-sections">
                                {/* Council Models */}
                                <div className="models-column">
                                    <h3>Council Models (2-5 required)</h3>

                                    {/* Selected Council Models Panel */}
                                    {councilModels.length > 0 && (
                                        <div className="selected-models-panel">
                                            <div className="panel-header">Selected ({councilModels.length}/5)</div>
                                            <div className="selected-models-list">
                                                {councilModels.map(modelId => {
                                                    const model = availableModels.find(m => m.id === modelId);
                                                    if (!model) return null;
                                                    return (
                                                        <div key={modelId} className="selected-model-item">
                                                            <span className="model-name">{model.name}</span>
                                                            <button
                                                                className="remove-model-btn"
                                                                onClick={() => toggleCouncilModel(modelId)}
                                                                title="Remove from selection"
                                                            >
                                                                ×
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {/* Available Council Models Panel */}
                                    <div className="available-models-panel">
                                        <div className="panel-header">
                                            Available Models {filteredModels.length > 0 && `(${filteredModels.filter(m => !councilModels.includes(m.id)).length})`}
                                        </div>
                                        <div className="model-list">
                                            {loading && <div className="loading-text">Loading models...</div>}
                                            {!loading && filteredModels.filter(m => !councilModels.includes(m.id)).length === 0 && (
                                                <div className="no-models">
                                                    {modelSearch || showFreeOnly
                                                        ? "No models match your search. Try adjusting filters."
                                                        : "All available models are selected."}
                                                </div>
                                            )}
                                            {filteredModels.filter(m => !councilModels.includes(m.id)).map(model => (
                                                <div key={model.id} className="model-item" onClick={() => toggleCouncilModel(model.id)}>
                                                    <span className="model-name">{model.name}</span>
                                                    {model.pricing && (
                                                        <span className="model-price">
                                                            {model.pricing.input === '0' ? 'FREE' : '$'}
                                                        </span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Chairman Model */}
                                <div className="models-column">
                                    <h3>Chairman Model (1 required)</h3>

                                    {/* Selected Chairman Panel */}
                                    {chairmanModel && (
                                        <div className="selected-models-panel">
                                            <div className="panel-header">Selected</div>
                                            <div className="selected-models-list">
                                                {(() => {
                                                    const model = availableModels.find(m => m.id === chairmanModel);
                                                    if (!model) return null;
                                                    return (
                                                        <div key={chairmanModel} className="selected-model-item">
                                                            <span className="model-name">{model.name}</span>
                                                            <button
                                                                className="remove-model-btn"
                                                                onClick={() => setChairmanModel('')}
                                                                title="Remove selection"
                                                            >
                                                                ×
                                                            </button>
                                                        </div>
                                                    );
                                                })()}
                                            </div>
                                        </div>
                                    )}

                                    {/* Available Chairman Models Panel */}
                                    <div className="available-models-panel">
                                        <div className="panel-header">
                                            Available Models {filteredModels.length > 0 && `(${filteredModels.filter(m => m.id !== chairmanModel).length})`}
                                        </div>
                                        <div className="model-list">
                                            {loading && <div className="loading-text">Loading models...</div>}
                                            {!loading && filteredModels.filter(m => m.id !== chairmanModel).length === 0 && (
                                                <div className="no-models">
                                                    {modelSearch || showFreeOnly
                                                        ? "No models match your search. Try adjusting filters."
                                                        : "Model already selected."}
                                                </div>
                                            )}
                                            {filteredModels.filter(m => m.id !== chairmanModel).map(model => (
                                                <div key={model.id} className="model-item" onClick={() => setChairmanModel(model.id)}>
                                                    <span className="model-name">{model.name}</span>
                                                    {model.pricing && (
                                                        <span className="model-price">
                                                            {model.pricing.input === '0' ? 'FREE' : '$'}
                                                        </span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="actions">
                                <button className="action-btn" onClick={handleSaveModels} disabled={loading}>Save Preferences</button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'apikey' && (
                        <div className="apikey-tab">
                            <p className="hint-text">
                                Enter your personal OpenRouter API key to use your own credits. Leave blank to use the system default.
                            </p>
                            <form onSubmit={handleSaveApiKey}>
                                <div className="form-group">
                                    <label>OpenRouter API Key</label>
                                    <input
                                        type="password"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                        placeholder="sk-or-v1-..."
                                    />
                                    {maskedApiKey && (
                                        <div className="current-key-display">
                                            Current Key: {maskedApiKey}
                                        </div>
                                    )}
                                </div>
                                <button type="submit" disabled={loading} className="action-btn">Save API Key</button>
                                {hasApiKey && (
                                    <button
                                        type="button"
                                        onClick={handleClearApiKey}
                                        disabled={loading}
                                        className="action-btn"
                                        style={{ marginTop: '10px', backgroundColor: '#e74c3c' }}
                                    >
                                        Clear My API Key
                                    </button>
                                )}
                            </form>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
