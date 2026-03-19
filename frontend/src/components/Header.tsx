'use client';

import { useState, useEffect, useRef } from 'react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';
import { 
  Code2, 
  Bot, 
  Settings, 
  User, 
  ChevronDown, 
  Moon, 
  Sun, 
  LogOut,
  BookOpen,
  BarChart3
} from 'lucide-react';

interface HeaderProps {
  className?: string;
}

export function Header({ className = '' }: HeaderProps) {
  const { state, logout } = useCodeCoach();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [currentMode, setCurrentMode] = useState<'practice' | 'compete' | 'learn'>('practice');
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  const modes = [
    { id: 'practice', label: 'Practice', icon: Code2, description: 'Solve coding problems' },
    { id: 'compete', label: 'Compete', icon: BarChart3, description: 'Join coding contests' },
    { id: 'learn', label: 'Learn', icon: BookOpen, description: 'Study algorithms' },
  ];

  return (
    <header className={`bg-gray-900 border-b border-gray-700 ${className}`}>
      <div className="flex items-center justify-between px-6 py-3">
        {/* Left Section - Logo and Navigation */}
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center">
              <Code2 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">CodeCoach AI</span>
          </div>

          {/* Mode Switcher */}
          <nav className="flex items-center space-x-1">
            {modes.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setCurrentMode(mode.id as any)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentMode === mode.id
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
                title={mode.description}
              >
                <mode.icon className="w-4 h-4" />
                <span>{mode.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Right Section - User Menu and Settings */}
        <div className="flex items-center space-x-4">
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            title="Toggle dark mode"
          >
            {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Settings */}
          <button
            className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>

          {/* User Menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
            >
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="hidden sm:block">
                {state.user?.name || 'Guest User'}
              </span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {/* Dropdown Menu */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-md shadow-lg py-1 z-50">
                <div className="px-4 py-2 border-b border-gray-700">
                  <p className="text-sm font-medium text-white">
                    {state.user?.name || 'Guest User'}
                  </p>
                  <p className="text-xs text-gray-400">
                    {state.user?.email || 'guest@example.com'}
                  </p>
                </div>

                <div className="py-1">
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
                    Profile
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
                    Settings
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors">
                    API Keys
                  </button>
                </div>

                <div className="border-t border-gray-700 py-1">
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-700 hover:text-red-300 transition-colors flex items-center space-x-2"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sub Navigation */}
      <div className="px-6 py-2 bg-gray-800 border-t border-gray-700">
        <div className="flex items-center space-x-6 text-sm">
          <button className="text-cyan-400 hover:text-cyan-300 transition-colors">
            Problems
          </button>
          <button className="text-gray-400 hover:text-white transition-colors">
            Submissions
          </button>
          <button className="text-gray-400 hover:text-white transition-colors">
            Leaderboard
          </button>
          <button className="text-gray-400 hover:text-white transition-colors">
            Discuss
          </button>
        </div>
      </div>
    </header>
  );
}