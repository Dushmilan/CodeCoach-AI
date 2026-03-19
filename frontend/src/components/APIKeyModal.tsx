'use client';

import { useState, useEffect } from 'react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';
import { X, Key, Eye, EyeOff } from 'lucide-react';

interface APIKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function APIKeyModal({ isOpen, onClose }: APIKeyModalProps) {
  const { state, setApiKey } = useCodeCoach();
  const [apiKey, setLocalApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setLocalApiKey(state.apiKey || '');
      setError('');
    }
  }, [isOpen, state.apiKey]);

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setError('API key is required');
      return;
    }

    setIsValidating(true);
    setError('');

    try {
      // TODO: Implement actual API key validation
      // For now, we'll just save it
      setApiKey(apiKey.trim());
      onClose();
    } catch (err) {
      setError('Invalid API key. Please check your NVIDIA NIM credentials.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div 
        className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl w-full max-w-md mx-4"
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
              <Key className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">NVIDIA NIM API Key</h2>
              <p className="text-sm text-gray-400">Configure your AI assistant access</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-gray-300 mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                id="api-key"
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  setLocalApiKey(e.target.value);
                  setError('');
                }}
                placeholder="Enter your NVIDIA NIM API key..."
                className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                disabled={isValidating}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute inset-y-0 right-0 px-3 flex items-center text-gray-400 hover:text-white"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-400">{error}</p>
            )}
          </div>

          <div className="text-sm text-gray-400 space-y-2">
            <p>
              <strong>Phase 1 Compatibility:</strong> This key enables basic AI assistance features.
            </p>
            <p>
              Your key is stored locally and never shared with our servers.
            </p>
            <p>
              <a 
                href="https://developer.nvidia.com/nim" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-green-400 hover:text-green-300 underline"
              >
                Get your NVIDIA NIM API key →
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 border border-gray-600 rounded-md hover:bg-gray-700 transition-colors"
            disabled={isValidating}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isValidating || !apiKey.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isValidating ? 'Validating...' : 'Save API Key'}
          </button>
        </div>
      </div>
    </div>
  );
}