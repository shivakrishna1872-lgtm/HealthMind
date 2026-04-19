import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const router = useRouter();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0A0A14' }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 100 }}>
        <Animated.View entering={FadeInUp.delay(100).springify()} style={{ marginBottom: 36 }}>
          <Text style={{ color: '#8E8E93', fontSize: 14, marginBottom: 4 }}>Welcome back</Text>
          <Text style={{ color: '#FFFFFF', fontSize: 30, fontWeight: '700' }}>HealthMind</Text>
          <Text style={{ color: '#8E8E93', fontSize: 15, marginTop: 6, lineHeight: 22 }}>
            AI-powered prescription safety agent
          </Text>
        </Animated.View>

        <Animated.Text entering={FadeInDown.delay(200)} style={{ color: '#8E8E93', fontSize: 12, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 14 }}>
          Quick actions
        </Animated.Text>

        {[
          { icon: 'shield-checkmark-outline', label: 'Run safety check', sub: 'Check a prescription against patient FHIR data', color: '#6C63FF', route: '/(tabs)/prescribe' },
          { icon: 'chatbubbles-outline',       label: 'Ask AI assistant',  sub: 'Chat about medications, conditions, or results',  color: '#00C896', route: '/(tabs)/chat'     },
          { icon: 'time-outline',              label: 'View history',      sub: 'Browse past safety checks and results',            color: '#FFB74D', route: '/(tabs)/history'  },
        ].map((item, i) => (
          <Animated.View key={item.label} entering={FadeInDown.delay(260 + i * 70)}>
            <TouchableOpacity
              onPress={() => router.push(item.route as any)}
              style={{
                backgroundColor: '#1A1A2E', borderRadius: 18, padding: 18,
                flexDirection: 'row', alignItems: 'center', gap: 16,
                marginBottom: 12, borderWidth: 1, borderColor: '#2A2A3E',
              }}
            >
              <View style={{ width: 48, height: 48, borderRadius: 14, backgroundColor: item.color + '22', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name={item.icon as any} size={24} color={item.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ color: '#FFFFFF', fontWeight: '600', fontSize: 15 }}>{item.label}</Text>
                <Text style={{ color: '#8E8E93', fontSize: 13, marginTop: 2 }}>{item.sub}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color="#3A3A5E" />
            </TouchableOpacity>
          </Animated.View>
        ))}

        <Animated.View entering={FadeInDown.delay(500)} style={{
          backgroundColor: '#6C63FF11', borderRadius: 16, padding: 16,
          borderWidth: 1, borderColor: '#6C63FF33', marginTop: 8,
          flexDirection: 'row', gap: 12, alignItems: 'flex-start',
        }}>
          <Ionicons name="person-outline" size={18} color="#6C63FF" style={{ marginTop: 2 }} />
          <Text style={{ color: '#A0A0CC', fontSize: 13, lineHeight: 20, flex: 1 }}>
            Human-in-the-Loop: Every AI safety recommendation requires physician review before any clinical action.
          </Text>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}