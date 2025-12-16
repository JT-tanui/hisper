import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false
  })
});

const NotificationService = {
  initialize: async (): Promise<void> => {
    const settings = await Notifications.getPermissionsAsync();
    if (!settings.granted) {
      await Notifications.requestPermissionsAsync();
    }
    await Notifications.setNotificationCategoryAsync('task-actions', [
      { identifier: 'retry', buttonTitle: 'Retry' },
      { identifier: 'reroute', buttonTitle: 'Reroute' },
      { identifier: 'schedule', buttonTitle: 'Schedule' }
    ]);
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX
      });
    }
  },
  sendLocalNotification: async (title: string, body: string): Promise<void> => {
    await Notifications.scheduleNotificationAsync({
      content: { title, body, categoryIdentifier: 'task-actions' },
      trigger: null
    });
  }
};

export default NotificationService;
