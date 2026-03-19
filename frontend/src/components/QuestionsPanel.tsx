'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, Clock, CheckCircle, Zap, Trophy } from 'lucide-react';

interface Question {
  id: string;
  title: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  category: string;
  acceptance: number;
  tags: string[];
  solved: boolean;
  timeLimit?: string;
}

const mockQuestions: Question[] = [
  {
    id: '1',
    title: 'Two Sum',
    difficulty: 'Easy',
    category: 'Array',
    acceptance: 47.8,
    tags: ['Array', 'Hash Table'],
    solved: true,
  },
  {
    id: '2',
    title: 'Add Two Numbers',
    difficulty: 'Medium',
    category: 'Linked List',
    acceptance: 39.2,
    tags: ['Linked List', 'Math', 'Recursion'],
    solved: false,
  },
  {
    id: '3',
    title: 'Longest Substring',
    difficulty: 'Medium',
    category: 'String',
    acceptance: 32.1,
    tags: ['Hash Table', 'String', 'Sliding Window'],
    solved: false,
  },
  {
    id: '4',
    title: 'Median of Two Arrays',
    difficulty: 'Hard',
    category: 'Array',
    acceptance: 35.7,
    tags: ['Array', 'Binary Search', 'Divide and Conquer'],
    solved: false,
  },
  {
    id: '5',
    title: 'Longest Palindrome',
    difficulty: 'Medium',
    category: 'String',
    acceptance: 31.5,
    tags: ['String', 'Dynamic Programming'],
    solved: true,
  },
];

const difficultyColors = {
  Easy: 'text-green-400 bg-green-400/10',
  Medium: 'text-yellow-400 bg-yellow-400/10',
  Hard: 'text-red-400 bg-red-400/10',
};

export default function QuestionsPanel() {
  const [questions, setQuestions] = useState<Question[]>(mockQuestions);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState<'all' | 'easy' | 'medium' | 'hard' | 'solved'>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = ['all', ...Array.from(new Set(questions.map(q => q.category)))];

  const filteredQuestions = questions.filter(question => {
    const matchesSearch = question.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         question.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesTab = selectedTab === 'all' || 
                      (selectedTab === 'solved' && question.solved) ||
                      question.difficulty.toLowerCase() === selectedTab;
    
    const matchesCategory = selectedCategory === 'all' || question.category === selectedCategory;
    
    return matchesSearch && matchesTab && matchesCategory;
  });

  const tabs = [
    { id: 'all', label: 'All', icon: Filter },
    { id: 'easy', label: 'Easy', icon: CheckCircle },
    { id: 'medium', label: 'Medium', icon: Clock },
    { id: 'hard', label: 'Hard', icon: Zap },
    { id: 'solved', label: 'Solved', icon: Trophy },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="h-full flex flex-col glass-morphism rounded-lg p-4"
    >
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gradient mb-2">Questions</h3>
        
        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search questions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500 transition-colors"
        >
          {categories.map(category => (
            <option key={category} value={category}>
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-4 bg-slate-800 rounded-lg p-1">
        {tabs.map(tab => (
          <motion.button
            key={tab.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`flex-1 flex items-center justify-center space-x-1 px-2 py-1 rounded-md text-xs transition-colors ${
              selectedTab === tab.id
                ? 'bg-cyan-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <tab.icon size={12} />
            <span>{tab.label}</span>
          </motion.button>
        ))}
      </div>

      {/* Questions List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <AnimatePresence>
          {filteredQuestions.map((question, index) => (
            <motion.div
              key={question.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.02, x: 5 }}
              className="mb-3 p-3 glass-morphism rounded-lg cursor-pointer hover:neon-glow transition-all duration-300"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="text-sm font-semibold text-slate-100 truncate">
                      {question.title}
                    </h4>
                    {question.solved && (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColors[question.difficulty]}`}>
                      {question.difficulty}
                    </span>
                    <span className="text-xs text-slate-400">{question.category}</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mb-2">
                    {question.tags.slice(0, 2).map(tag => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {question.tags.length > 2 && (
                      <span className="text-xs text-slate-400">+{question.tags.length - 2}</span>
                    )}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-xs text-slate-400">
                    {question.acceptance.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500">acceptance</div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Stats */}
      <div className="mt-auto pt-3 border-t border-slate-700">
        <div className="flex justify-between text-xs text-slate-400">
          <span>{filteredQuestions.length} questions</span>
          <span>
            {questions.filter(q => q.solved).length}/{questions.length} solved
          </span>
        </div>
      </div>
    </motion.div>
  );
}