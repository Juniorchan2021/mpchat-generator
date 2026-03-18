"""
Tests for core/ideation.py

测试策略：
- build_ideation_prompt() 纯单元测试（无 LLM 调用）
- parse_topics() 纯单元测试（无 LLM 调用）
- generate_topics() mock call_llm，避免真实 API 调用
"""
import json
import pytest
from unittest.mock import patch


# ══════════════════════════════════════════════════════════════════
# build_ideation_prompt() 测试
# ══════════════════════════════════════════════════════════════════

class TestBuildIdeationPrompt:
    def setup_method(self):
        from core.ideation import build_ideation_prompt
        self.build = build_ideation_prompt

    def test_returns_two_messages(self):
        """必须返回 [system, user] 两条消息"""
        msgs = self.build("crypto payment", "", 20)
        assert isinstance(msgs, list)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_keyword_in_user_message(self):
        """核心关键词必须出现在 user 消息中"""
        msgs = self.build("stablecoin wallet", "", 20)
        assert "stablecoin wallet" in msgs[1]["content"]

    def test_count_in_prompt(self):
        """生成数量必须出现在提示词中"""
        msgs = self.build("crypto payment", "", 30)
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "30" in full

    def test_industry_in_prompt_when_provided(self):
        """提供 industry 时必须出现在提示词中"""
        msgs = self.build("payment", "fintech", 20)
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "fintech" in full

    def test_industry_empty_no_crash(self):
        """industry 为空时不应报错"""
        msgs = self.build("payment", "", 20)
        assert len(msgs) == 2

    def test_requires_json_output_in_system(self):
        """System prompt 必须要求输出 JSON"""
        msgs = self.build("crypto", "", 20)
        system = msgs[0]["content"]
        assert "json" in system.lower() or "JSON" in system

    def test_required_fields_in_system(self):
        """System prompt 必须包含 title/search_intent/difficulty/keywords 字段说明"""
        msgs = self.build("crypto", "", 20)
        system = msgs[0]["content"].lower()
        for field in ("title", "search_intent", "difficulty", "keywords"):
            assert field in system, f"缺少字段: {field}"

    def test_empty_keyword_raises(self):
        """空关键词应抛出 ValueError"""
        with pytest.raises(ValueError, match="core_keyword"):
            self.build("", "", 20)

    def test_whitespace_keyword_raises(self):
        """纯空格关键词应抛出 ValueError"""
        with pytest.raises(ValueError, match="core_keyword"):
            self.build("   ", "", 20)

    def test_count_must_be_positive(self):
        """count <= 0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="count"):
            self.build("crypto", "", 0)

    def test_count_max_50(self):
        """count > 50 应抛出 ValueError"""
        with pytest.raises(ValueError, match="count"):
            self.build("crypto", "", 51)

    def test_messages_content_are_strings(self):
        """所有消息的 content 必须是非空字符串"""
        msgs = self.build("crypto payment", "", 20)
        for m in msgs:
            assert isinstance(m["content"], str)
            assert len(m["content"]) > 0

    def test_chinese_keyword_auto_generates_chinese_title(self):
        """中文关键词在 auto 模式下应指定生成中文标题"""
        msgs = self.build("加密支付", "", 20, language="auto")
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "中文" in full

    def test_english_keyword_auto_generates_english_title(self):
        """英文关键词在 auto 模式下应指定生成英文标题"""
        msgs = self.build("crypto payment", "", 20, language="auto")
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "English" in full

    def test_language_zh_forces_chinese(self):
        """language='zh' 强制中文输出"""
        msgs = self.build("crypto payment", "", 20, language="zh")
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "中文" in full

    def test_language_en_forces_english(self):
        """language='en' 强制英文输出"""
        msgs = self.build("加密支付", "", 20, language="en")
        full = msgs[0]["content"] + msgs[1]["content"]
        assert "English" in full


# ══════════════════════════════════════════════════════════════════
# parse_topics() 测试
# ══════════════════════════════════════════════════════════════════

SAMPLE_TOPICS_JSON = json.dumps([
    {"title": "What is Crypto Payment?", "search_intent": "informational", "difficulty": "easy", "keywords": ["crypto", "payment"]},
    {"title": "Best Stablecoin Wallets 2025", "search_intent": "commercial", "difficulty": "medium", "keywords": ["stablecoin", "wallet"]},
])

class TestParseTopics:
    def setup_method(self):
        from core.ideation import parse_topics
        self.parse = parse_topics

    def test_parses_clean_json_array(self):
        """标准 JSON 数组应直接解析"""
        result = self.parse(SAMPLE_TOPICS_JSON)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parses_json_with_markdown_fence(self):
        """被 ```json 包裹的数组也应正确解析"""
        wrapped = f"```json\n{SAMPLE_TOPICS_JSON}\n```"
        result = self.parse(wrapped)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parses_json_embedded_in_text(self):
        """JSON 数组嵌入在文字中也应提取"""
        text = f"以下是选题建议：\n{SAMPLE_TOPICS_JSON}\n希望对你有帮助。"
        result = self.parse(text)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_each_topic_has_required_fields(self):
        """每个 topic 都应有 title, search_intent, difficulty, keywords"""
        result = self.parse(SAMPLE_TOPICS_JSON)
        for item in result:
            assert "title" in item
            assert "search_intent" in item
            assert "difficulty" in item
            assert "keywords" in item

    def test_empty_string_returns_empty_list(self):
        """空字符串应返回空列表，不抛出异常"""
        result = self.parse("")
        assert result == []

    def test_invalid_json_returns_empty_list(self):
        """无法解析的字符串应返回空列表，不抛出异常"""
        result = self.parse("这不是 JSON 内容 !@#$")
        assert result == []

    def test_not_array_returns_empty_list(self):
        """非数组 JSON（如 dict）应返回空列表"""
        result = self.parse('{"title": "test"}')
        assert result == []

    def test_keywords_field_always_list(self):
        """keywords 字段应始终为列表"""
        result = self.parse(SAMPLE_TOPICS_JSON)
        for item in result:
            assert isinstance(item["keywords"], list)


# ══════════════════════════════════════════════════════════════════
# generate_topics() 集成测试（mock call_llm）
# ══════════════════════════════════════════════════════════════════

MOCK_LLM_RESPONSE = SAMPLE_TOPICS_JSON

class TestGenerateTopics:
    def setup_method(self):
        from core.ideation import generate_topics
        self.generate = generate_topics

    @patch("core.ideation.call_llm")
    def test_returns_list_of_topics(self, mock_llm):
        """正常调用应返回 topic 列表"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        result = self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="crypto payment", industry="", count=20,
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    @patch("core.ideation.call_llm")
    def test_call_llm_invoked_once(self, mock_llm):
        """call_llm 应仅被调用一次"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="crypto payment", industry="", count=20,
        )
        mock_llm.assert_called_once()

    @patch("core.ideation.call_llm")
    def test_industry_passed_to_llm(self, mock_llm):
        """industry 应传递到 LLM"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="payment", industry="fintech", count=20,
        )
        call_args = mock_llm.call_args
        messages = call_args.kwargs.get("messages") or call_args.args[4]
        full_text = " ".join(m["content"] for m in messages)
        assert "fintech" in full_text

    def test_empty_api_key_raises(self):
        """空 api_key 应抛出 ValueError"""
        with pytest.raises(ValueError, match="api_key"):
            self.generate(
                provider="openai", api_key="", base_url="", model="gpt-4o",
                core_keyword="crypto", industry="", count=20,
            )

    def test_empty_keyword_raises(self):
        """空 core_keyword 应抛出 ValueError"""
        with pytest.raises(ValueError, match="core_keyword"):
            self.generate(
                provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
                core_keyword="", industry="", count=20,
            )

    @patch("core.ideation.call_llm")
    def test_empty_llm_response_returns_empty_list(self, mock_llm):
        """LLM 返回空字符串时应返回空列表，不抛出"""
        mock_llm.return_value = ""
        result = self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="crypto", industry="", count=20,
        )
        assert result == []

    @patch("core.ideation.call_llm")
    def test_malformed_llm_response_returns_empty_list(self, mock_llm):
        """LLM 返回无法解析的内容时应返回空列表，不抛出"""
        mock_llm.return_value = "抱歉，我无法完成这个请求。"
        result = self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="crypto", industry="", count=20,
        )
        assert result == []

    @patch("core.ideation.call_llm")
    def test_provider_passed_to_llm(self, mock_llm):
        """provider 应正确传递给 call_llm"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        self.generate(
            provider="anthropic", api_key="sk-ant-test", base_url="", model="claude-3-5-sonnet",
            core_keyword="crypto", industry="", count=20,
        )
        call_kwargs = mock_llm.call_args
        assert call_kwargs.kwargs.get("provider") == "anthropic" or call_kwargs.args[0] == "anthropic"

    @patch("core.ideation.call_llm")
    def test_language_passed_to_prompt(self, mock_llm):
        """language 参数应影响 messages 中的语言指令"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="加密支付", industry="", count=20, language="zh",
        )
        call_args = mock_llm.call_args
        messages = call_args.kwargs.get("messages") or call_args.args[4]
        full_text = " ".join(m["content"] for m in messages)
        assert "中文" in full_text

    @patch("core.ideation.call_llm")
    def test_auto_language_detects_chinese(self, mock_llm):
        """auto 模式下，中文关键词应触发中文标题指令"""
        mock_llm.return_value = MOCK_LLM_RESPONSE
        self.generate(
            provider="openai", api_key="sk-test", base_url="", model="gpt-4o",
            core_keyword="稳定币钱包", industry="", count=20, language="auto",
        )
        call_args = mock_llm.call_args
        messages = call_args.kwargs.get("messages") or call_args.args[4]
        full_text = " ".join(m["content"] for m in messages)
        assert "中文" in full_text
