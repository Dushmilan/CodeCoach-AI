'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Zap, Activity, Thermometer, Gauge } from 'lucide-react';

interface GPUMetrics {
  gpu: number;
  memory: number;
  temperature: number;
  power: number;
  vram: number;
}

interface AIMetrics {
  tokensPerSecond: number;
  model: string;
  status: string;
  inferenceTime: number;
}

export default function AIDashboard() {
  const [gpuMetrics, setGpuMetrics] = useState<GPUMetrics>({
    gpu: 45,
    memory: 62,
    temperature: 72,
    power: 180,
    vram: 78,
  });

  const [aiMetrics, setAiMetrics] = useState<AIMetrics>({
    tokensPerSecond: 156,
    model: 'GPT-4 Turbo',
    status: 'Active',
    inferenceTime: 0.8,
  });

  // Simulate real-time metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setGpuMetrics(prev => ({
        gpu: Math.max(20, Math.min(95, prev.gpu + (Math.random() - 0.5) * 5)),
        memory: Math.max(30, Math.min(90, prev.memory + (Math.random() - 0.5) * 3)),
        temperature: Math.max(60, Math.min(85, prev.temperature + (Math.random() - 0.5) * 2)),
        power: Math.max(120, Math.min(250, prev.power + (Math.random() - 0.5) * 10)),
        vram: Math.max(50, Math.min(95, prev.vram + (Math.random() - 0.5) * 4)),
      }));

      setAiMetrics(prev => ({
        ...prev,
        tokensPerSecond: Math.max(100, Math.min(200, prev.tokensPerSecond + (Math.random() - 0.5) * 10)),
        inferenceTime: Math.max(0.3, Math.min(2.0, prev.inferenceTime + (Math.random() - 0.5) * 0.1)),
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const MetricCard = ({ 
    icon: Icon, 
    label, 
    value, 
    unit, 
    color,
    maxValue = 100 
  }: {
    icon: React.ElementType;
    label: string;
    value: number;
    unit: string;
    color: string;
    maxValue?: number;
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-morphism rounded-lg p-4 hover:neon-glow transition-all duration-300"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className={`w-4 h-4 ${color}`} />
          <span className="text-sm text-slate-300">{label}</span>
        </div>
        <span className={`text-sm font-bold ${color}`}>
          {value.toFixed(1)}{unit}
        </span>
      </div>
      
      <div className="w-full bg-slate-800 rounded-full h-1.5">
        <motion.div
          className={`h-1.5 rounded-full ${color.replace('text-', 'bg-')}`}
          initial={{ width: 0 }}
          animate={{ width: `${(value / maxValue) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="h-full flex flex-col space-y-4"
    >
      {/* Header */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-gradient mb-2">AI Dashboard</h2>
        <p className="text-sm text-slate-400">Real-time GPU & AI Metrics</p>
      </div>

      {/* AI Model Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="hologram-effect rounded-lg p-4"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-300">Model</span>
          <span className="text-sm font-bold text-cyan-400">{aiMetrics.model}</span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-slate-300">Status</span>
          <span className="text-sm font-bold text-green-400 flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></div>
            {aiMetrics.status}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-300">Inference</span>
          <span className="text-sm font-bold text-cyan-400">{aiMetrics.inferenceTime}s</span>
        </div>
      </motion.div>

      {/* GPU Metrics */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-slate-200 mb-3">GPU Metrics</h3>
        
        <MetricCard
          icon={Cpu}
          label="GPU Usage"
          value={gpuMetrics.gpu}
          unit="%"
          color="text-cyan-400"
        />
        
        <MetricCard
          icon={Zap}
          label="Memory"
          value={gpuMetrics.memory}
          unit="%"
          color="text-blue-400"
        />
        
        <MetricCard
          icon={Thermometer}
          label="Temperature"
          value={gpuMetrics.temperature}
          unit="°C"
          color="text-orange-400"
          maxValue={100}
        />
        
        <MetricCard
          icon={Activity}
          label="Power"
          value={gpuMetrics.power}
          unit="W"
          color="text-purple-400"
          maxValue={300}
        />
        
        <MetricCard
          icon={Gauge}
          label="VRAM"
          value={gpuMetrics.vram}
          unit="%"
          color="text-pink-400"
        />
      </div>

      {/* Performance Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-morphism rounded-lg p-4"
      >
        <h4 className="text-sm font-semibold text-slate-200 mb-2">Performance</h4>
        <div className="text-center">
          <div className="text-2xl font-bold text-gradient">
            {aiMetrics.tokensPerSecond.toFixed(0)}
          </div>
          <div className="text-xs text-slate-400">tokens/sec</div>
        </div>
      </motion.div>

      {/* Holographic Effect Overlay */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 rounded-lg animate-pulse" />
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse" />
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse" />
      </div>
    </motion.div>
  );
}