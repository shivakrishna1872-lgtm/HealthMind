import { Tabs } from 'expo-router';
import { Platform, View } from 'react-native';
import { BlurView } from 'expo-blur';
import { Ionicons } from '@expo/vector-icons';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

const ACCENT = '#6C63FF';
const INACTIVE = '#8E8E93';

function TabIcon({ name, focused }: { name: any; focused: boolean }) {
  const scale = useSharedValue(focused ? 1.2 : 1);
  scale.value = withSpring(focused ? 1.2 : 1, { damping: 12, stiffness: 180 });
  const style = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <Animated.View style={style}>
      <Ionicons name={name} size={24} color={focused ? ACCENT : INACTIVE} />
    </Animated.View>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          position: 'absolute',
          borderTopWidth: 0,
          backgroundColor: Platform.OS === 'ios' ? 'transparent' : '#0F0F1A',
          elevation: 0,
        },
        tabBarBackground: () =>
          Platform.OS === 'ios' ? (
            <BlurView intensity={80} tint="dark" style={{ flex: 1 }} />
          ) : (
            <View style={{ flex: 1, backgroundColor: '#0F0F1A' }} />
          ),
        tabBarActiveTintColor: ACCENT,
        tabBarInactiveTintColor: INACTIVE,
        tabBarLabelStyle: { fontSize: 11, fontWeight: '500', marginBottom: 4 },
      }}
    >
      <Tabs.Screen name="index"    options={{ title: 'Home',     tabBarIcon: ({ focused }) => <TabIcon name={focused ? 'home' : 'home-outline'} focused={focused} /> }} />
      <Tabs.Screen name="prescribe" options={{ title: 'Safety',   tabBarIcon: ({ focused }) => <TabIcon name={focused ? 'shield-checkmark' : 'shield-checkmark-outline'} focused={focused} /> }} />
      <Tabs.Screen name="chat"     options={{ title: 'Assistant', tabBarIcon: ({ focused }) => <TabIcon name={focused ? 'chatbubbles' : 'chatbubbles-outline'} focused={focused} /> }} />
      <Tabs.Screen name="history"  options={{ title: 'History',   tabBarIcon: ({ focused }) => <TabIcon name={focused ? 'time' : 'time-outline'} focused={focused} /> }} />
    </Tabs>
  );
}