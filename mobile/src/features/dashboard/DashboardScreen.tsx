import React, { useCallback, useMemo } from 'react';
import { FlatList, Text, TouchableOpacity, View, useColorScheme } from 'react-native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { loadTasks, persistTasks } from '../../storage/offlineCache';
import useWebSocket from '../../hooks/useWebSocket';
import NotificationService from '../notifications/NotificationService';

interface TaskItem {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  updatedAt: string;
}

const DashboardScreen = (): JSX.Element => {
  const colorScheme = useColorScheme();
  const queryClient = useQueryClient();

  const { data: tasks = [] } = useQuery<TaskItem[]>(['tasks'], async () => {
    const cached = await loadTasks();
    if (cached.length) {
      return cached as TaskItem[];
    }
    const response = await apiClient.get('/tasks');
    await persistTasks(response.data);
    return response.data;
  });

  const mutation = useMutation({
    mutationFn: (payload: { id: string; action: 'retry' | 'reroute' | 'schedule' }) =>
      apiClient.post(`/tasks/${payload.id}/${payload.action}`),
    onSuccess: (_, variables) => {
      NotificationService.sendLocalNotification('Task action', `${variables.action} sent for task ${variables.id}`);
    }
  });

  const websocketUrl = useMemo(() => 'wss://api.hisper.local/tasks', []);

  const onSocketMessage = useCallback(
    async (payload: unknown) => {
      const current = queryClient.getQueryData<TaskItem[]>(['tasks']) ?? [];
      const next = [...current];
      const update = payload as TaskItem;
      const idx = next.findIndex((task) => task.id === update.id);
      if (idx >= 0) {
        next[idx] = update;
      } else {
        next.push(update);
      }
      queryClient.setQueryData(['tasks'], next);
      await persistTasks(next);
      if (update.status === 'completed' || update.status === 'failed') {
        NotificationService.sendLocalNotification('Task updated', `${update.name} is ${update.status}`);
      }
    },
    [queryClient]
  );

  useWebSocket({ url: websocketUrl, onMessage: onSocketMessage });

  const renderTask = ({ item }: { item: TaskItem }): JSX.Element => (
    <View
      accessible
      accessibilityLabel={`Task ${item.name} status ${item.status}`}
      style={{ padding: 12, borderRadius: 12, backgroundColor: colorScheme === 'dark' ? '#1f2937' : '#fff', marginBottom: 12 }}
    >
      <Text style={{ color: colorScheme === 'dark' ? '#e2e8f0' : '#0f172a', fontWeight: '700', fontSize: 16 }}>{item.name}</Text>
      <Text style={{ color: colorScheme === 'dark' ? '#a5b4fc' : '#2563eb', marginVertical: 4 }}>Status: {item.status}</Text>
      <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
        {(['retry', 'reroute', 'schedule'] as const).map((action) => (
          <TouchableOpacity
            key={action}
            onPress={() => mutation.mutate({ id: item.id, action })}
            accessibilityLabel={`${action} task`}
            style={{ backgroundColor: '#2563eb', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 10 }}
          >
            <Text style={{ color: '#fff', fontWeight: '600' }}>{action}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  return (
    <View style={{ flex: 1, padding: 16, backgroundColor: colorScheme === 'dark' ? '#0f172a' : '#e2e8f0' }}>
      <FlatList
        accessibilityLabel="Task dashboard"
        data={tasks}
        keyExtractor={(item) => item.id}
        renderItem={renderTask}
      />
    </View>
  );
};

export default DashboardScreen;
