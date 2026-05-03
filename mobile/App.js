import React, { useEffect, useState } from 'react';
import { StatusBar, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import DashboardScreen from './src/screens/DashboardScreen';
import TradesScreen from './src/screens/TradesScreen';
import PlaceTradeScreen from './src/screens/PlaceTradeScreen';
import StatsScreen from './src/screens/StatsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { loadApiUrl } from './src/api/client';
import { COLORS } from './src/theme';

const Tab = createBottomTabNavigator();

const NAV_THEME = {
  dark: true,
  colors: {
    primary: COLORS.accent,
    background: COLORS.background,
    card: COLORS.card,
    text: COLORS.text,
    border: COLORS.border,
    notification: COLORS.accent,
  },
};

const TAB_ICONS = {
  Dashboard: ['home', 'home-outline'],
  Trade:     ['flash', 'flash-outline'],
  Trades:    ['list', 'list-outline'],
  Stats:     ['bar-chart', 'bar-chart-outline'],
  Settings:  ['settings', 'settings-outline'],
};

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadApiUrl().then(() => setReady(true));
  }, []);

  if (!ready) return <View style={{ flex: 1, backgroundColor: COLORS.background }} />;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar barStyle="light-content" backgroundColor={COLORS.background} />
        <NavigationContainer theme={NAV_THEME}>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                const [active, inactive] = TAB_ICONS[route.name] || ['help', 'help-outline'];
                return <Ionicons name={focused ? active : inactive} size={size} color={color} />;
              },
              tabBarActiveTintColor: COLORS.tabActive,
              tabBarInactiveTintColor: COLORS.tabInactive,
              tabBarStyle: {
                backgroundColor: COLORS.card,
                borderTopColor: COLORS.border,
                borderTopWidth: 1,
              },
              tabBarLabelStyle: { fontSize: 10, fontWeight: '600' },
              headerStyle: { backgroundColor: COLORS.card, shadowColor: 'transparent', elevation: 0 },
              headerTintColor: COLORS.text,
              headerTitleStyle: { fontWeight: '700', fontSize: 17 },
            })}
          >
            <Tab.Screen
              name="Dashboard"
              component={DashboardScreen}
              options={{ headerShown: false }}
            />
            <Tab.Screen
              name="Trade"
              component={PlaceTradeScreen}
              options={{
                headerShown: false,
                tabBarLabel: 'Trade',
                // Highlight the Trade tab to make it stand out
                tabBarIcon: ({ focused, size }) => (
                  <Ionicons
                    name={focused ? 'flash' : 'flash-outline'}
                    size={size + 2}
                    color={focused ? COLORS.accent : COLORS.tabInactive}
                  />
                ),
              }}
            />
            <Tab.Screen
              name="Trades"
              component={TradesScreen}
              options={{ title: 'History' }}
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
