import React, { useEffect } from 'react';
import { Appearance, useColorScheme } from 'react-native';
import { NavigationContainer, DefaultTheme, DarkTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { focusManager } from '@tanstack/react-query';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StatusBar } from 'expo-status-bar';
import ChatScreen from './src/features/chat/ChatScreen';
import DashboardScreen from './src/features/dashboard/DashboardScreen';
import VoiceScreen from './src/features/voice/VoiceScreen';
import AuthProvider from './src/features/auth/AuthProvider';
import { queryClient, persister } from './src/state/queryClient';
import NotificationService from './src/features/notifications/NotificationService';

const Tab = createBottomTabNavigator();

const App = (): JSX.Element => {
  const colorScheme = useColorScheme();

  useEffect(() => {
    const subscription = Appearance.addChangeListener(({ colorScheme: scheme }) => {
      const isFocused = true;
      if (isFocused) {
        focusManager.setFocused(scheme !== undefined);
      }
    });
    NotificationService.initialize();
    return () => subscription.remove();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AuthProvider>
          <PersistQueryClientProvider client={queryClient} persistOptions={{ persister }}>
            <NavigationContainer theme={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
              <StatusBar style={colorScheme === 'dark' ? 'light' : 'dark'} />
              <Tab.Navigator screenOptions={{ headerShown: false }}>
                <Tab.Screen name="Chat" component={ChatScreen} />
                <Tab.Screen name="Tasks" component={DashboardScreen} />
                <Tab.Screen name="Voice" component={VoiceScreen} />
              </Tab.Navigator>
            </NavigationContainer>
          </PersistQueryClientProvider>
        </AuthProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

export default App;
