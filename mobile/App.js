import React, { useEffect, useState } from 'react';
import { StatusBar, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import DashboardScreen from './src/screens/DashboardScreen';
import TradesScreen from './src/screens/TradesScreen';
import StatsScreen from './src/screens/StatsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { loadApiUrl } from './src/api/client';
import { COLORS } from './src/theme';

const Tab = createBottomTabNavigator();

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Pre-load saved API URL before rendering
    loadApiUrl().then(() => setReady(true));
  }, []);

  if (!ready) return <View style={{ flex: 1, backgroundColor: COLORS.background }} />;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar barStyle="light-content" backgroundColor={COLORS.background} />
        <NavigationContainer
          theme={{
            dark: true,
            colors: {
              primary: COLORS.accent,
              background: COLORS.background,
              card: COLORS.card,
              text: COLORS.text,
              border: COLORS.border,
              notification: COLORS.accent,
            },
          }}
        >
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                const icons = {
                  Dashboard: focused ? 'home' : 'home-outline',
                  Trades: focused ? 'list' : 'list-outline',
                  Stats: focused ? 'bar-chart' : 'bar-chart-outline',
                  Settings: focused ? 'settings' : 'settings-outline',
                };
                return <Ionicons name={icons[route.name]} size={size} color={color} />;
              },
              tabBarActiveTintColor: COLORS.tabActive,
              tabBarInactiveTintColor: COLORS.tabInactive,
              tabBarStyle: {
                backgroundColor: COLORS.card,
                borderTopColor: COLORS.border,
                borderTopWidth: 1,
              },
              tabBarLabelStyle: {
                fontSize: 11,
                fontWeight: '600',
              },
              headerStyle: {
                backgroundColor: COLORS.card,
                shadowColor: 'transparent',
                elevation: 0,
              },
              headerTintColor: COLORS.text,
              headerTitleStyle: {
                fontWeight: '700',
                fontSize: 17,
              },
            })}
          >
            <Tab.Screen
              name="Dashboard"
              component={DashboardScreen}
              options={{ headerShown: false }}
            />
            <Tab.Screen
              name="Trades"
              component={TradesScreen}
              options={{ title: 'Trade History' }}
            />
            <Tab.Screen
              name="Stats"
              component={StatsScreen}
              options={{ headerShown: false }}
            />
            <Tab.Screen
              name="Settings"
              component={SettingsScreen}
              options={{ headerShown: false }}
            />
          </Tab.Navigator>
        </NavigationContainer>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
