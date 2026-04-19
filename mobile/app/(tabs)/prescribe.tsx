import { useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import Animated, { FadeInDown, FadeIn } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { safetyCheckService } from '../../services/safetyCheck';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';
import { SAMPLE_FHIR } from '../../constants/sampleFhir';

type CheckStatus = 'idle' | 'checking' | 'done' | 'error';

const STATUS_CONFIG = {
  BLOCK: { color: '#FF6B6B', bg: '#FF6B6B11', border: '#FF6B6B33', icon: 'ban-outline',              label: 'Contraindicated — Do not prescribe' },
  WARN:  { color: '#FFB74D', bg: '#FFB74D11', border: '#FFB74D33', icon: 'warning-outline',           label: 'Caution — Review required'          },
  ALLOW: { color: '#00C896', bg: '#00C89611', border: '#00C89633', icon: 'checkmark-circle-outline',  label: 'No major contraindications'         },
};

export default function PrescribeScreen() {
  const [medication, setMedication] = useState('');
  const [fhirJson, setFhirJson]     = useState('');
  const [useSample, setUseSample]   = useState(true);
  const [checkState, setCheckState] = useState<CheckStatus>('idle');
  const [result, setResult]         = useState<any>(null);
  const [error, setError]           = useState('');

  const runCheck = useCallback(async () => {
    if (!medication.trim()) return;
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setCheckState('checking'); setResult(null); setError('');
    try {
      const fhir = useSample ? JSON.stringify(SAMPLE_FHIR) : fhirJson;
      const res = await safetyCheckService.check({ proposed_medication: medication.trim(), patient_fhir_json: fhir });
      setResult(res); setCheckState('done');
      await Haptics.notificationAsync(
        res.status === 'BLOCK' ? Haptics.NotificationFeedbackType.Error
        : res.status === 'WARN' ? Haptics.NotificationFeedbackType.Warning
        : Haptics.NotificationFeedbackType.Success
      );
    } catch (e: any) {
      setCheckState('error'); setError(e.message ?? 'Safety check failed');
    }
  }, [medication, fhirJson, useSample]);

  const cfg = result ? STATUS_CONFIG[result.status as keyof typeof STATUS_CONFIG] : null;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0A0A14' }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 100 }}>
          <Animated.Text entering={FadeInDown.delay(100)} style={{ color: '#FFFFFF', fontSize: 28, fontWeight: '700', marginBottom: 8 }}>Safety check</Animated.Text>
          <Animated.Text entering={FadeInDown.delay(160)} style={{ color: '#8E8E93', fontSize: 15, marginBottom: 28, lineHeight: 22 }}>
            Enter a proposed medication and patient FHIR data to run a full AI safety evaluation.
          </Animated.Text>

          <Animated.View entering={FadeInDown.delay(220)} style={{ marginBottom: 16 }}>
            <Text style={{ color: '#8E8E93', fontSize: 12, fontWeight: '600', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Proposed medication</Text>
            <TextInput value={medication} onChangeText={setMedication} placeholder="e.g. Ibuprofen, Metformin, Warfarin..." placeholderTextColor="#3A3A5E"
              style={{ backgroundColor: '#1A1A2E', borderRadius: 14, padding: 16, color: '#FFFFFF', fontSize: 16, borderWidth: 1, borderColor: medication ? '#6C63FF55' : '#2A2A3E' }}
              autoCapitalize="words" />
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(280)} style={{ marginBottom: 24 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Text style={{ color: '#8E8E93', fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 }}>Patient FHIR data</Text>
              <TouchableOpacity onPress={() => setUseSample(!useSample)}
                style={{ backgroundColor: useSample ? '#6C63FF22' : '#2A2A3E', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1, borderColor: useSample ? '#6C63FF55' : '#3A3A5E' }}>
                <Text style={{ color: useSample ? '#6C63FF' : '#8E8E93', fontSize: 12, fontWeight: '600' }}>{useSample ? 'Using sample patient' : 'Use sample'}</Text>
              </TouchableOpacity>
            </View>
            {useSample ? (
              <View style={{ backgroundColor: '#1A1A2E', borderRadius: 14, padding: 14, borderWidth: 1, borderColor: '#2A2A3E' }}>
                <Text style={{ color: '#8E8E93', fontSize: 13 }}>Sample: Jane Doe · Stage 3 CKD · Lisinopril + Furosemide</Text>
              </View>
            ) : (
              <TextInput value={fhirJson} onChangeText={setFhirJson} placeholder="Paste FHIR R4 Bundle JSON..." placeholderTextColor="#3A3A5E" multiline
                style={{ backgroundColor: '#1A1A2E', borderRadius: 14, padding: 16, color: '#FFFFFF', fontSize: 13, borderWidth: 1, borderColor: '#2A2A3E', minHeight: 120, textAlignVertical: 'top' }} />
            )}
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(340)}>
            <TouchableOpacity onPress={runCheck} disabled={!medication.trim() || checkState === 'checking'}
              style={{ backgroundColor: medication.trim() && checkState !== 'checking' ? '#6C63FF' : '#1A1A2E', borderRadius: 16, padding: 18, alignItems: 'center', marginBottom: 24 }}>
              <Text style={{ color: '#FFFFFF', fontWeight: '700', fontSize: 16 }}>
                {checkState === 'checking' ? 'Running safety check...' : 'Run safety check'}
              </Text>
            </TouchableOpacity>
          </Animated.View>

          {checkState === 'checking' && (
            <Animated.View entering={FadeIn} style={{ gap: 12 }}>
              <SkeletonLoader height={80} borderRadius={16} />
              <SkeletonLoader height={120} borderRadius={16} />
            </Animated.View>
          )}

          {checkState === 'done' && result && cfg && (
            <Animated.View entering={FadeIn.duration(400)} style={{ gap: 14 }}>
              <View style={{ backgroundColor: cfg.bg, borderRadius: 16, padding: 20, borderWidth: 1, borderColor: cfg.border, flexDirection: 'row', alignItems: 'center', gap: 14 }}>
                <Ionicons name={cfg.icon as any} size={32} color={cfg.color} />
                <View style={{ flex: 1 }}>
                  <Text style={{ color: cfg.color, fontWeight: '700', fontSize: 18 }}>{result.status}</Text>
                  <Text style={{ color: cfg.color + 'CC', fontSize: 13, marginTop: 2 }}>{cfg.label}</Text>
                </View>
              </View>
              <View style={{ backgroundColor: '#1A1A2E', borderRadius: 14, padding: 16, borderWidth: 1, borderColor: '#2A2A3E' }}>
                <Text style={{ color: '#8E8E93', fontSize: 11, fontWeight: '600', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Clinical rationale</Text>
                <Text style={{ color: '#CCCCDD', fontSize: 14, lineHeight: 22 }}>{result.reason}</Text>
              </View>
              {result.patient_conditions?.length > 0 && (
                <View style={{ backgroundColor: '#1A1A2E', borderRadius: 14, padding: 16, borderWidth: 1, borderColor: '#2A2A3E', gap: 8 }}>
                  <Text style={{ color: '#8E8E93', fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 }}>Patient context</Text>
                  {result.patient_conditions.map((c: string, i: number) => <Text key={i} style={{ color: '#CCCCDD', fontSize: 13 }}>• {c}</Text>)}
                  {result.current_medications?.map((m: string, i: number) => <Text key={i} style={{ color: '#8E8E93', fontSize: 13 }}>· {m}</Text>)}
                </View>
              )}
              <View style={{ backgroundColor: '#6C63FF11', borderRadius: 14, padding: 14, borderWidth: 1, borderColor: '#6C63FF33', flexDirection: 'row', gap: 10 }}>
                <Ionicons name="person-outline" size={16} color="#6C63FF" style={{ marginTop: 2 }} />
                <Text style={{ color: '#A0A0CC', fontSize: 13, lineHeight: 18, flex: 1 }}>
                  Human-in-the-Loop: This recommendation requires physician review and approval before any clinical action.
                </Text>
              </View>
            </Animated.View>
          )}

          {checkState === 'error' && (
            <Animated.View entering={FadeIn} style={{ backgroundColor: '#FF6B6B11', borderRadius: 14, padding: 16, borderWidth: 1, borderColor: '#FF6B6B33' }}>
              <Text style={{ color: '#FF6B6B', fontWeight: '600', marginBottom: 4 }}>Check failed</Text>
              <Text style={{ color: '#FF6B6B99', fontSize: 13 }}>{error}</Text>
            </Animated.View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}