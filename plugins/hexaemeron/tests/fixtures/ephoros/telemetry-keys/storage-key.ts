// A storage key is a storage key, not a telemetry sink.
localStorage.setItem(`${TIMESTAMP_KEY}_${address.toLowerCase()}`, String(Date.now()))
