"use client";

import { Button } from "@/components/ui/button";
import { useLocalStorage } from "@/hooks";
import {
  ChevronLeft,
  ChevronRight,
  Code,
  Lightbulb,
  MessageSquare,
  Settings,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

const STEPS = [
  {
    title: "Welcome to CodeCoach AI",
    description:
      "Practice coding interview questions with instant feedback, AI coaching, and progress tracking.",
    icon: Lightbulb,
  },
  {
    title: "Question Browser",
    description:
      "Browse coding questions by difficulty or category. Click any question to view its description, examples, and hints in the sidebar.",
    icon: Code,
  },
  {
    title: "AI Coach",
    description:
      "Get 24/7 AI-powered help. Ask for hints, code reviews, explanations, or debugging assistance. The AI understands your code context.",
    icon: MessageSquare,
  },
  {
    title: "NVIDIA API Key",
    description:
      "Open Settings and add your free NVIDIA API key to enable the AI Coach. Your key stays in your browser — never sent to our server.",
    icon: Settings,
  },
];

export function OnboardingTour() {
  const [showTour, setShowTour] = useLocalStorage("onboarding-done", false);
  const [step, setStep] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || showTour) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      setShowTour(true);
    } else {
      setStep((s) => s + 1);
    }
  };

  const handleDismiss = () => {
    setShowTour(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-xl shadow-2xl max-w-md w-full mx-4 p-6 space-y-6">
        <div className="flex justify-between items-start">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <current.icon className="h-6 w-6 text-primary" />
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-secondary rounded transition-colors"
            aria-label="Dismiss tour"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-semibold">{current.title}</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {current.description}
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === step ? "bg-primary" : "bg-muted-foreground/30"
                }`}
              />
            ))}
          </div>

          <div className="flex gap-2">
            {step > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setStep((s) => s - 1)}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {isLast ? "Get started" : "Next"}
              {!isLast && <ChevronRight className="h-4 w-4 ml-1" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
