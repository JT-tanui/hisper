import AsyncStorage from '@react-native-async-storage/async-storage';
import { QueryClient } from '@tanstack/react-query';
import { PersistedClient, Persister } from '@tanstack/react-query-persist-client';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      cacheTime: 1000 * 60 * 60,
      staleTime: 1000 * 15,
      retry: 2
    }
  }
});

const persister: Persister<PersistedClient> = createAsyncStoragePersister({
  storage: AsyncStorage,
  key: 'hisper-cache'
});

export { persister };
