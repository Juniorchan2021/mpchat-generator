"""
Tests for core/translate.py

测试策略：
- build_translate_prompt() 使用纯单元测试（无需 LLM 调用）
- translate_article() 使用 unittest.mock patch call_llm，避免真实 API 调用
"""
import pytest
from unittest.mock import patch, MagicMock


# ──────────────────────────────────────────────
# build_translate_prompt() 单元测试
# ──────────────────────────────────────────────

class TestBuildTranslatePrompt:
    def setup_method(self):
        from core.translate import build_translate_prompt
        self.build = build_translate_prompt

    def test_returns_two_messages(self):
        """必须返回包含 system + user 两条消息的列表"""
        messages = self.build("# Hello\nSome text.", "中文", "英文")
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_article_embedded_in_user_message(self):
        """原文必须出现在 user 消息中"""
        article = "# MPChat 简介\n这是一篇测试文章。"
        messages = self.build(article, "中文", "英文")
        assert article in messages[1]["content"]

    def test_target_lang_in_prompt(self):
        """目标语言必须出现在提示词中"""
        messages = self.build("# Test", "中文", "繁体中文")
        full_text = messages[0]["content"] + messages[1]["content"]
        assert "繁体中文" in full_text

    def test_source_lang_in_prompt(self):
        """原文语言必须出现在提示词中"""
        messages = self.build("# Test", "中文", "英文")
        full_text = messages[0]["content"] + messages[1]["content"]
        assert "中文" in full_text

    def test_markdown_preservation_instruction(self):
        """System prompt 必须明确要求保留 Markdown 格式"""
        messages = self.build("# Test", "中文", "英文")
        system_content = messages[0]["content"]
        assert "Markdown" in system_content or "markdown" in system_content

    def test_heading_preservation_instruction(self):
        """System prompt 必须要求保留标题层级"""
        messages = self.build("# Test", "中文", "英文")
        system_content = messages[0]["content"]
        assert any(kw in system_content for kw in ["标题", "H1", "H2", "heading", "#"])

    def test_empty_article_raises(self):
        """空文章应抛出 ValueError"""
        with pytest.raises(ValueError, match="article"):
            self.build("", "中文", "英文")

    def test_whitespace_only_article_raises(self):
        """纯空白文章应抛出 ValueError"""
        with pytest.raises(ValueError, match="article"):
            self.build("   \n\t  ", "中文", "英文")

    def test_same_source_target_raises(self):
        """源语言与目标语言相同时应抛出 ValueError"""
        with pytest.raises(ValueError, match="source_lang"):
            self.build("# Test", "英文", "英文")

    def test_empty_target_lang_raises(self):
        """目标语言为空应抛出 ValueError"""
        with pytest.raises(ValueError, match="target_lang"):
            self.build("# Test", "中文", "")

    def test_empty_source_lang_raises(self):
        """源语言为空应抛出 ValueError"""
        with pytest.raises(ValueError, match="source_lang"):
            self.build("# Test", "", "英文")

    def test_message_content_are_strings(self):
        """所有消息的 content 字段必须是字符串"""
        messages = self.build("# Test article", "中文", "英文")
        for msg in messages:
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0


# ──────────────────────────────────────────────
# translate_article() 集成测试（mock call_llm）
# ──────────────────────────────────────────────

SAMPLE_ARTICLE_ZH = """# MPChat：加密支付的未来

## 什么是 MPChat？

MPChat 是一款革命性的加密钱包应用。

## 核心功能

- 稳定币支付
- 多链支持
- 简单易用

## 总结

立即前往 mp.net 下载 MPChat！
"""

SAMPLE_ARTICLE_EN = """# MPChat: The Future of Crypto Payments

## What is MPChat?

MPChat is a revolutionary crypto wallet application.

## Core Features

- Stablecoin payments
- Multi-chain support
- Easy to use

## Conclusion

Visit mp.net now to download MPChat!
"""


class TestTranslateArticle:
    def setup_method(self):
        from core.translate import translate_article
        self.translate = translate_article

    @patch("core.translate.call_llm")
    def test_returns_translated_string(self, mock_llm):
        """正常翻译应返回非空字符串"""
        mock_llm.return_value = SAMPLE_ARTICLE_EN
        result = self.translate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            article=SAMPLE_ARTICLE_ZH,
            source_lang="中文",
            target_lang="英文",
        )
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    @patch("core.translate.call_llm")
    def test_call_llm_is_invoked_once(self, mock_llm):
        """call_llm 应仅被调用一次"""
        mock_llm.return_value = SAMPLE_ARTICLE_EN
        self.translate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            article=SAMPLE_ARTICLE_ZH,
            source_lang="中文",
            target_lang="英文",
        )
        mock_llm.assert_called_once()

    @patch("core.translate.call_llm")
    def test_call_llm_receives_correct_provider(self, mock_llm):
        """call_llm 应使用传入的 provider"""
        mock_llm.return_value = SAMPLE_ARTICLE_EN
        self.translate(
            provider="anthropic",
            api_key="sk-ant-test",
            base_url="",
            model="claude-3-5-sonnet",
            article=SAMPLE_ARTICLE_ZH,
            source_lang="中文",
            target_lang="英文",
        )
        call_kwargs = mock_llm.call_args
        assert call_kwargs.kwargs.get("provider") == "anthropic" or call_kwargs.args[0] == "anthropic"

    @patch("core.translate.call_llm")
    def test_strips_code_fences_from_result(self, mock_llm):
        """若 LLM 返回内容被 ``` 包裹，应自动剥离"""
        mock_llm.return_value = "```markdown\n" + SAMPLE_ARTICLE_EN + "\n```"
        result = self.translate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            article=SAMPLE_ARTICLE_ZH,
            source_lang="中文",
            target_lang="英文",
        )
        assert not result.startswith("```")
        assert not result.endswith("```")

    @patch("core.translate.call_llm")
    def test_empty_llm_response_raises(self, mock_llm):
        """LLM 返回空字符串时应抛出 ValueError"""
        mock_llm.return_value = ""
        with pytest.raises(ValueError):
            self.translate(
                provider="openai",
                api_key="sk-test",
                base_url="",
                model="gpt-4o",
                article=SAMPLE_ARTICLE_ZH,
                source_lang="中文",
                target_lang="英文",
            )

    @patch("core.translate.call_llm")
    def test_whitespace_only_llm_response_raises(self, mock_llm):
        """LLM 返回纯空白时应抛出 ValueError"""
        mock_llm.return_value = "   \n   "
        with pytest.raises(ValueError):
            self.translate(
                provider="openai",
                api_key="sk-test",
                base_url="",
                model="gpt-4o",
                article=SAMPLE_ARTICLE_ZH,
                source_lang="中文",
                target_lang="英文",
            )

    def test_empty_article_raises_before_llm(self):
        """空文章应在调用 LLM 前就抛出 ValueError"""
        with pytest.raises(ValueError, match="article"):
            self.translate(
                provider="openai",
                api_key="sk-test",
                base_url="",
                model="gpt-4o",
                article="",
                source_lang="中文",
                target_lang="英文",
            )

    def test_missing_api_key_raises_before_llm(self):
        """空 api_key 应抛出 ValueError"""
        with pytest.raises(ValueError, match="api_key"):
            self.translate(
                provider="openai",
                api_key="",
                base_url="",
                model="gpt-4o",
                article=SAMPLE_ARTICLE_ZH,
                source_lang="中文",
                target_lang="英文",
            )
