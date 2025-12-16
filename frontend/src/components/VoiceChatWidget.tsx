import React, { useEffect, useRef, useState } from 'react'
import { Mic, Square, Play, Pause, Waves, Loader2, History } from 'lucide-react'

interface VoiceHistoryMessage {
  id: number
  role: string
  content: string
  pinned?: boolean
  created_at: string
  audio_blob_id?: number | null
}

const VoiceChatWidget: React.FC = () => {
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [chunks, setChunks] = useState<Blob[]>([])
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [transcript, setTranscript] = useState('')
  const [history, setHistory] = useState<VoiceHistoryMessage[]>([])
  const [volume, setVolume] = useState(0)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const rafRef = useRef<number | null>(null)

  const apiKey = import.meta.env.VITE_VOICE_API_KEY || 'your-secret-key-change-in-production'

  const startConversation = async () => {
    const form = new FormData()
    if (conversationId) form.append('conversation_id', conversationId.toString())
    const response = await fetch('/api/v1/voice/start', {
      method: 'POST',
      headers: { 'X-API-Key': apiKey },
      body: form,
    })
    const data = await response.json()
    setConversationId(data.conversation_id)
    localStorage.setItem('hisper.conversationId', data.conversation_id)
  }

  const loadHistory = async (conversation: number) => {
    setLoadingHistory(true)
    try {
      const response = await fetch('/api/v1/chat/history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ conversation_id: conversation, max_tokens: 800 }),
      })
      if (response.ok) {
        const data = await response.json()
        setHistory(data.messages)
      }
    } finally {
      setLoadingHistory(false)
    }
  }

  useEffect(() => {
    const stored = localStorage.getItem('hisper.conversationId')
    if (stored) {
      const id = parseInt(stored)
      setConversationId(id)
      loadHistory(id)
    } else {
      startConversation()
    }
    // Cleanup analyser
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      analyserRef.current?.disconnect()
    }
  }, [])

  const updateVolume = () => {
    if (!analyserRef.current) return
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteTimeDomainData(dataArray)
    let sum = 0
    for (let i = 0; i < dataArray.length; i++) {
      const value = dataArray[i] - 128
      sum += value * value
    }
    const rms = Math.sqrt(sum / dataArray.length)
    setVolume(Math.min(1, rms / 64))
    rafRef.current = requestAnimationFrame(updateVolume)
  }

  const startRecording = async () => {
    if (isRecording) return
    await startConversation()
    setTranscript('')
    setChunks([])
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    setMediaRecorder(recorder)

    const audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    analyserRef.current = analyser
    updateVolume()

    recorder.ondataavailable = async (event) => {
      if (event.data.size > 0) {
        setChunks((prev) => [...prev, event.data])
        await streamChunk(event.data)
      }
    }

    recorder.start(500)
    setIsRecording(true)
  }

  const streamChunk = async (blob: Blob) => {
    if (!conversationId) return
    const formData = new FormData()
    formData.append('conversation_id', conversationId.toString())
    formData.append('role', 'user')
    formData.append('provider', 'openai')
    formData.append('audio', blob, 'chunk.webm')

    const response = await fetch('/api/v1/voice/stream', {
      method: 'POST',
      headers: { 'X-API-Key': apiKey },
      body: formData,
    })

    const reader = response.body?.getReader()
    if (reader) {
      const decoder = new TextDecoder()
      const { value } = await reader.read()
      if (value) {
        const parsed = JSON.parse(decoder.decode(value))
        if (parsed.transcript_chunk) {
          setTranscript((prev) => `${prev} ${parsed.transcript_chunk}`.trim())
        }
      }
    }
  }

  const stopRecording = async () => {
    mediaRecorder?.stop()
    setIsRecording(false)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    analyserRef.current?.disconnect()

    const blob = new Blob(chunks, { type: 'audio/webm' })
    const url = URL.createObjectURL(blob)
    setAudioUrl(url)

    if (conversationId) {
      const formData = new FormData()
      formData.append('conversation_id', conversationId.toString())
      formData.append('provider', 'openai')
      formData.append('transcript', transcript || 'Captured voice input')
      await fetch('/api/v1/voice/stop', {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
        body: formData,
      })
      loadHistory(conversationId)
    }
  }

  const togglePlayback = () => {
    if (!audioRef.current) return
    if (audioRef.current.paused) {
      audioRef.current.play()
      setIsPlaying(true)
    } else {
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Waves className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Voice Chat</h3>
        </div>
        <span className="text-xs text-gray-500">conversation #{conversationId ?? '…'}</span>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`flex items-center px-4 py-2 rounded-lg text-white transition-colors ${
            isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isRecording ? <Square className="w-4 h-4 mr-2" /> : <Mic className="w-4 h-4 mr-2" />}
          {isRecording ? 'Stop' : 'Record'}
        </button>
        <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-green-500 transition-all" style={{ width: `${volume * 100}%` }} />
        </div>
        <span className="text-sm text-gray-600">{(volume * 100).toFixed(0)}%</span>
      </div>

      {audioUrl && (
        <div className="flex items-center space-x-3 bg-gray-50 p-3 rounded-lg">
          <button
            onClick={togglePlayback}
            className="p-2 bg-white rounded-full shadow hover:shadow-md"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <audio ref={audioRef} src={audioUrl} onEnded={() => setIsPlaying(false)} />
          <div className="text-sm text-gray-700">Latest recording</div>
        </div>
      )}

      <div className="bg-gray-50 p-3 rounded-lg min-h-[80px] text-sm text-gray-800 whitespace-pre-wrap">
        {transcript || 'Streaming transcript will appear here...'}
      </div>

      <div className="border-t pt-3">
        <div className="flex items-center space-x-2 mb-2 text-gray-700">
          <History className="w-4 h-4" />
          <span className="text-sm font-semibold">Recent conversation</span>
          {loadingHistory && <Loader2 className="w-4 h-4 animate-spin" />}
        </div>
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {history.map((msg) => (
            <div key={msg.id} className="text-xs p-2 rounded bg-white border border-gray-200">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">{msg.role}</span>
                <span className="text-gray-500">{new Date(msg.created_at).toLocaleTimeString()}</span>
              </div>
              <div className="text-gray-700 whitespace-pre-wrap">{msg.content}</div>
            </div>
          ))}
          {!history.length && (
            <div className="text-xs text-gray-500">No conversation history yet.</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VoiceChatWidget
