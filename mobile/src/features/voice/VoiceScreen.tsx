import React, { useState } from 'react';
import { Text, TouchableOpacity, View, useColorScheme } from 'react-native';
import * as Speech from 'expo-speech';
import { apiClient } from '../../api/client';

const VoiceScreen = (): JSX.Element => {
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const colorScheme = useColorScheme();

  const sendVoiceCommand = async (): Promise<void> => {
    if (!transcript) {
      return;
    }
    const { data } = await apiClient.post('/voice/command', { transcript });
    setResponse(data.reply);
    Speech.speak(data.reply, { language: 'en-US' });
  };

  const mockCapture = (): void => {
    const sample = 'Check running tasks and read latest chat summary';
    setTranscript(sample);
    Speech.speak('Captured voice command');
  };

  return (
    <View style={{ flex: 1, padding: 16, backgroundColor: colorScheme === 'dark' ? '#0f172a' : '#f8fafc' }}>
      <Text
        accessibilityLabel="Voice transcript"
        style={{ color: colorScheme === 'dark' ? '#e2e8f0' : '#0f172a', marginBottom: 12 }}
      >
        Transcript: {transcript || 'Tap capture to speak'}
      </Text>
      <TouchableOpacity
        accessibilityLabel="Capture voice command"
        onPress={mockCapture}
        style={{ backgroundColor: '#0ea5e9', padding: 16, borderRadius: 12, marginBottom: 12 }}
      >
        <Text style={{ color: '#fff', fontWeight: '700' }}>Capture Voice</Text>
      </TouchableOpacity>
      <TouchableOpacity
        accessibilityLabel="Send voice command"
        onPress={sendVoiceCommand}
        style={{ backgroundColor: '#16a34a', padding: 16, borderRadius: 12, marginBottom: 12 }}
      >
        <Text style={{ color: '#fff', fontWeight: '700' }}>Send Command</Text>
      </TouchableOpacity>
      <TouchableOpacity
        accessibilityLabel="Play response"
        onPress={() => Speech.speak(response)}
        style={{ backgroundColor: '#2563eb', padding: 16, borderRadius: 12 }}
      >
        <Text style={{ color: '#fff', fontWeight: '700' }}>Play Response</Text>
      </TouchableOpacity>
      <Text style={{ color: colorScheme === 'dark' ? '#cbd5e1' : '#1f2937', marginTop: 16 }}>Response: {response}</Text>
    </View>
  );
};

export default VoiceScreen;
