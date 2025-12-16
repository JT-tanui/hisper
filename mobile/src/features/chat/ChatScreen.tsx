import React, { useCallback, useMemo, useState } from 'react';
import { FlatList, Text, TextInput, TouchableOpacity, View, useColorScheme } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { loadChatHistory, persistChatHistory } from '../../storage/offlineCache';
import useWebSocket from '../../hooks/useWebSocket';
import { useAuth } from '../auth/AuthProvider';

interface ChatMessage {
  id: string;
  sender: string;
  content: string;
  createdAt: string;
}

const ChatScreen = (): JSX.Element => {
  const [input, setInput] = useState('');
  const queryClient = useQueryClient();
  const { token } = useAuth();
  const colorScheme = useColorScheme();

  const { data: messages = [] } = useQuery<ChatMessage[]>(['chat-history'], async () => {
    const cached = await loadChatHistory();
    if (cached.length) {
      return cached as ChatMessage[];
    }
    const response = await apiClient.get('/chat/history');
    await persistChatHistory(response.data);
    return response.data;
  });

  const mutation = useMutation({
    mutationFn: async (body: { content: string }) => apiClient.post('/chat/send', body),
    onSuccess: async (_, variables) => {
      const optimistic: ChatMessage = {
        id: `${Date.now()}`,
        sender: 'me',
        content: variables.content,
        createdAt: new Date().toISOString()
      };
      const current = queryClient.getQueryData<ChatMessage[]>(['chat-history']) ?? [];
      const next = [...current, optimistic];
      queryClient.setQueryData(['chat-history'], next);
      await persistChatHistory(next);
    }
  });

  const websocketUrl = useMemo(() => `wss://api.hisper.local/chat?token=${token ?? ''}`, [token]);

  const onSocketMessage = useCallback(
    async (payload: unknown) => {
      const current = queryClient.getQueryData<ChatMessage[]>(['chat-history']) ?? [];
      const next = [...current, payload as ChatMessage];
      queryClient.setQueryData(['chat-history'], next);
      await persistChatHistory(next);
    },
    [queryClient]
  );

  useWebSocket({ url: websocketUrl, onMessage: onSocketMessage });

  const sendMessage = (): void => {
    if (!input.trim()) {
      return;
    }
    mutation.mutate({ content: input });
    setInput('');
  };

  return (
    <View style={{ flex: 1, padding: 16, backgroundColor: colorScheme === 'dark' ? '#0f172a' : '#f8fafc' }}>
      <FlatList
        accessibilityLabel="Chat history"
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={{ marginVertical: 6 }}>
            <Text style={{ color: colorScheme === 'dark' ? '#e2e8f0' : '#0f172a', fontWeight: '600' }}>{item.sender}</Text>
            <Text style={{ color: colorScheme === 'dark' ? '#cbd5e1' : '#1f2937' }}>{item.content}</Text>
          </View>
        )}
      />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <TextInput
          accessibilityLabel="Type a message"
          style={{ flex: 1, borderRadius: 12, borderWidth: 1, borderColor: '#94a3b8', padding: 12, color: colorScheme === 'dark' ? '#e2e8f0' : '#0f172a' }}
          onChangeText={setInput}
          value={input}
          placeholder="Message"
          placeholderTextColor={colorScheme === 'dark' ? '#94a3b8' : '#94a3b8'}
        />
        <TouchableOpacity
          accessibilityLabel="Send message"
          accessibilityHint="Double tap to send the current message"
          onPress={sendMessage}
          style={{ backgroundColor: '#2563eb', paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12 }}
        >
          <Text style={{ color: '#fff', fontWeight: '700' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ChatScreen;
