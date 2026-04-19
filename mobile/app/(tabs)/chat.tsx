import { useState, useRef, useCallback, useEffect } from 'react';
import { View, Text, TextInput, FlatList, KeyboardAvoidingView, Platform, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import Animated, { FadeInDown, FadeInUp, Layout } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../../store/chatStore';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { TypingIndicator } from '../../components/chat/TypingIndicator';
import { QuickReplies } from '../../components/chat/QuickReplies';
import axios from 'axios';

const MCP_URL = process.env.EXPO_PUBLIC_MCP_URL ?? 'http://localhost:8000';

const QUICK_REPLIES = [
  'What are common NSAID contraindications?',
  'Explain Stage 3 CKD risks',
  'What is HITL validation?',
  'How does openFDA work?',
];

export default function ChatScreen() {
  const flatListRef = useRef<FlatList>(null);
  const { messages, addMessage, setTyping, isTyping, sessionId } = useChatStore();
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const scrollToBottom = useCallback(() => { setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100); }, []);
  useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

  const sendMessage = useCallback(async (text: string) => {
    const msg = text.trim();
    if (!msg || sending) return;
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSending(true); setInput('');
    addMessage({ role: 'user', content: msg, id: Date.now().toString() });
    setTyping(true); scrollToBottom();
    try {
      const res = await axios.post(`${MCP_URL}/chat`, { message: msg, session_id: sessionId, history: messages.slice(-10) }, { timeout: 60000 });
      setTyping(false);
      addMessage({ role: 'assistant', content: res.data.message, id: Date.now().toString() });
    } catch {
      setTyping(false);
      addMessage({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', id: Date.now().toString() });
    } finally { setSending(false); }
  }, [messages, sending, sessionId, addMessage, setTyping, scrollToBottom]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0A0A14' }} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <Animated.View entering={FadeInDown.delay(100)} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 20, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#1A1A2E' }}>
          <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: '#6C63FF22', alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="medical" size={20} color="#6C63FF" />
          </View>
          <View>
            <Text style={{ color: '#FFFFFF', fontWeight: '600', fontSize: 16 }}>HealthMind AI</Text>
            <Text style={{ color: '#00C896', fontSize: 12 }}>{isTyping ? 'Typing...' : 'Online'}</Text>
          </View>
        </Animated.View>

        <FlatList ref={flatListRef} data={messages} keyExtractor={m => m.id}
          contentContainerStyle={{ padding: 16, paddingBottom: 8, gap: 8 }}
          showsVerticalScrollIndicator={false}
          renderItem={({ item, index }) => (
            <Animated.View entering={FadeInUp.delay(index < 10 ? 0 : 50).springify()} layout={Layout.springify()}>
              <MessageBubble message={item} />
            </Animated.View>
          )}
          ListEmptyComponent={
            <Animated.View entering={FadeInDown.delay(200)} style={{ alignItems: 'center', marginTop: 60, gap: 16 }}>
              <View style={{ width: 72, height: 72, borderRadius: 20, backgroundColor: '#6C63FF22', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name="chatbubbles-outline" size={36} color="#6C63FF" />
              </View>
              <Text style={{ color: '#FFFFFF', fontSize: 18, fontWeight: '600', textAlign: 'center' }}>Ask your health assistant</Text>
              <Text style={{ color: '#8E8E93', fontSize: 14, textAlign: 'center', lineHeight: 20, maxWidth: 280 }}>
                Ask about medications, drug interactions, patient conditions, or safety protocols.
              </Text>
            </Animated.View>
          }
          ListFooterComponent={isTyping ? <TypingIndicator /> : null}
        />

        <QuickReplies replies={QUICK_REPLIES} onSelect={sendMessage} />

        <View style={{ flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#1A1A2E', gap: 10 }}>
          <TextInput value={input} onChangeText={setInput} placeholder="Ask about medications or safety..." placeholderTextColor="#3A3A5E" multiline
            style={{ flex: 1, backgroundColor: '#1A1A2E', borderRadius: 20, paddingHorizontal: 18, paddingVertical: 12, color: '#FFFFFF', fontSize: 15, maxHeight: 120, borderWidth: 1, borderColor: '#2A2A3E' }}
            returnKeyType="send" onSubmitEditing={() => sendMessage(input)} blurOnSubmit={false} />
          <Pressable onPress={() => sendMessage(input)} disabled={!input.trim() || sending}
            style={{ width: 46, height: 46, borderRadius: 23, backgroundColor: input.trim() && !sending ? '#6C63FF' : '#1A1A2E', alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="send" size={20} color={input.trim() && !sending ? '#FFFFFF' : '#3A3A5E'} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}