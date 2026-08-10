"use client";

import { DebriefFeature } from "@/features/debrief/debrief.types";
import { MissionCompleteOverlay } from "./MissionCompleteOverlay";
import { DebriefDialogue } from "./DebriefDialogue";
import { DebriefReportView } from "./DebriefReport";

export function MissionDebrief(props: DebriefFeature) {
  const { phase } = props;

  if (phase === "idle") return null;

  if (phase === "mission-complete") {
    return (
      <MissionCompleteOverlay
        onStart={props.startDebrief}
        onSkip={props.closeDebrief}
      />
    );
  }

  if (phase === "dialogue") {
    if (!props.context) return null;
    return (
      <DebriefDialogue
        context={props.context}
        currentQuestion={props.currentQuestion}
        isTyping={props.isTyping}
        round={props.round}
        totalRounds={props.totalRounds}
        isLastRound={props.isLastRound}
        onSubmitExplanation={props.submitExplanation}
        onNotSure={props.submitNotSure}
        onFinish={props.finishDebrief}
        onClose={props.closeDebrief}
      />
    );
  }

  if (phase === "report") {
    if (!props.report) return null;
    return (
      <DebriefReportView
        report={props.report}
        loading={props.reportLoading}
        onClose={props.closeDebrief}
      />
    );
  }

  return null;
}
