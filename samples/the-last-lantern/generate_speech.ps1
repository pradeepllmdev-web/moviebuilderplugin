$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$samplePlan = Get-Content (Join-Path $PSScriptRoot 'movie.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'audio') | Out-Null
foreach ($shot in $samplePlan.shots) {
    $sampleVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $sampleVoice.SelectVoice($shot.voice)
        $sampleVoice.Rate = -1
        $sampleVoice.SetOutputToWaveFile((Join-Path $PSScriptRoot ('audio/line_' + $shot.id + '.wav')))
        $sampleVoice.Speak($shot.text)
    } finally {
        $sampleVoice.Dispose()
    }
}
