`wake-gate`: ask out loud after a wake word you chose. Audio before it is
never transcribed, kept or sent: a state machine ported from willow-mcp's
voice ingress membrane, openWakeWord's wake word pipeline run through
onnxruntime, and faster-whisper over a model on this machine. It fetches
nothing and writes nothing; what it heard is printed for you to ask.
