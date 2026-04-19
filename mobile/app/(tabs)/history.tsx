import { View, Text, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useReportStore } from '../../store/reportStore';
import { format } from 'date-fns';

export default function HistoryScreen() {
  const { reports } = useReportStore();
  const STATUS_COLOR: Record<string, string> = { BLOCK: '#FF6B6B', WARN: '#FFB74D', ALLOW: '#00C896' };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0A0A14' }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 20, paddingBottom: 12 }}>
        <Animated.Text entering={FadeInDown.delay(100)} style={{ color: '#FFFFFF', fontSize: 28, fontWeight: '700' }}>History</Animated.Text>
        <Animated.Text entering={FadeInDown.delay(160)} style={{ color: '#8E8E93', fontSize: 15, marginTop: 4 }}>{reports.length} safety checks</Animated.Text>
      </View>
      <FlatList data={reports} keyExtractor={r => r.id}
        contentContainerStyle={{ padding: 20, paddingBottom: 100, gap: 12 }}
        ListEmptyComponent={
          <Animated.View entering={FadeInDown.delay(200)} style={{ alignItems: 'center', marginTop: 60, gap: 16 }}>
            <Ionicons name="shield-outline" size={56} color="#3A3A5E" />
            <Text style={{ color: '#8E8E93', fontSize: 16, textAlign: 'center' }}>No checks yet.{'\n'}Run your first safety check to get started.</Text>
          </Animated.View>
        }
        renderItem={({ item: r, index }) => (
          <Animated.View entering={FadeInDown.delay(200 + index * 60)}>
            <View style={{ backgroundColor: '#1A1A2E', borderRadius: 16, padding: 16, borderWidth: 1, borderColor: '#2A2A3E' }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: STATUS_COLOR[r.riskLevel ?? 'ALLOW'] ?? '#00C896' }} />
                <Text style={{ color: '#FFFFFF', fontWeight: '600', fontSize: 15, flex: 1 }}>{r.name}</Text>
                <Text style={{ color: STATUS_COLOR[r.riskLevel ?? 'ALLOW'] ?? '#00C896', fontWeight: '700', fontSize: 13 }}>{r.riskLevel ?? 'ALLOW'}</Text>
              </View>
              {r.summary ? <Text style={{ color: '#8E8E93', fontSize: 13, lineHeight: 18, marginBottom: 6 }} numberOfLines={2}>{r.summary}</Text> : null}
              <Text style={{ color: '#3A3A5E', fontSize: 11 }}>{format(new Date(r.createdAt), 'MMM d, yyyy · h:mm a')}</Text>
            </View>
          </Animated.View>
        )}
      />
    </SafeAreaView>
  );
}