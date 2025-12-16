import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEYS = {
  chatHistory: 'hisper-chat-history',
  taskSnapshots: 'hisper-task-cache'
};

const persistChatHistory = async (messages: unknown[]): Promise<void> => {
  await AsyncStorage.setItem(CACHE_KEYS.chatHistory, JSON.stringify(messages));
};

const loadChatHistory = async (): Promise<unknown[]> => {
  const raw = await AsyncStorage.getItem(CACHE_KEYS.chatHistory);
  return raw ? JSON.parse(raw) : [];
};

const persistTasks = async (tasks: unknown[]): Promise<void> => {
  await AsyncStorage.setItem(CACHE_KEYS.taskSnapshots, JSON.stringify(tasks));
};

const loadTasks = async (): Promise<unknown[]> => {
  const raw = await AsyncStorage.getItem(CACHE_KEYS.taskSnapshots);
  return raw ? JSON.parse(raw) : [];
};

export { persistChatHistory, loadChatHistory, persistTasks, loadTasks, CACHE_KEYS };
