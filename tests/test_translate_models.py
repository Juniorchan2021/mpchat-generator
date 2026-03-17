"""
Tests for TranslateRequest / TranslateResponse Pydantic models
"""
import pytest
from pydantic import ValidationError


class TestTranslateRequest:
    def setup_method(self):
        from api.models.requests import TranslateRequest
        self.Model = TranslateRequest

    def test_valid_minimal(self):
        """最小合法请求"""
        req = self.Model(
            api_key="sk-test",
            article="# Hello\nSome content.",
            source_lang="中文",
            target_lang="英文",
        )
        assert req.api_key == "sk-test"
        assert req.source_lang == "中文"
        assert req.target_lang == "英文"

    def test_defaults(self):
        """provider / model / base_url 有合理默认值"""
        req = self.Model(
            api_key="sk-test",
            article="# Hello",
            source_lang="中文",
            target_lang="英文",
        )
        assert isinstance(req.provider, str) and req.provider
        assert isinstance(req.model, str) and req.model
        assert isinstance(req.base_url, str)

    def test_empty_api_key_rejected(self):
        """空 api_key 被 Pydantic 校验拒绝"""
        with pytest.raises(ValidationError):
            self.Model(
                api_key="",
                article="# Hello",
                source_lang="中文",
                target_lang="英文",
            )

    def test_empty_article_rejected(self):
        """空 article 被 Pydantic 校验拒绝"""
        with pytest.raises(ValidationError):
            self.Model(
                api_key="sk-test",
                article="",
                source_lang="中文",
                target_lang="英文",
            )

    def test_empty_source_lang_rejected(self):
        """空 source_lang 被 Pydantic 校验拒绝"""
        with pytest.raises(ValidationError):
            self.Model(
                api_key="sk-test",
                article="# Hello",
                source_lang="",
                target_lang="英文",
            )

    def test_empty_target_lang_rejected(self):
        """空 target_lang 被 Pydantic 校验拒绝"""
        with pytest.raises(ValidationError):
            self.Model(
                api_key="sk-test",
                article="# Hello",
                source_lang="中文",
                target_lang="",
            )

    def test_article_max_length(self):
        """article 超过 100000 字符应被拒绝"""
        with pytest.raises(ValidationError):
            self.Model(
                api_key="sk-test",
                article="x" * 100001,
                source_lang="中文",
                target_lang="英文",
            )

    def test_custom_provider_and_model(self):
        """可以自定义 provider 和 model"""
        req = self.Model(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test",
            base_url="",
            article="# Hello",
            source_lang="中文",
            target_lang="英文",
        )
        assert req.provider == "anthropic"
        assert req.model == "claude-3-5-sonnet-20241022"

    def test_has_all_required_fields(self):
        """模型包含所有 SPEC 要求的字段"""
        req = self.Model(
            api_key="sk-test",
            article="# Hello",
            source_lang="中文",
            target_lang="英文",
        )
        for field in ("provider", "model", "api_key", "base_url", "article", "source_lang", "target_lang"):
            assert hasattr(req, field), f"缺少字段: {field}"


class TestTranslateResponse:
    def setup_method(self):
        from api.models.responses import TranslateResponse
        self.Model = TranslateResponse

    def test_valid_response(self):
        """合法响应可以构建"""
        resp = self.Model(
            translated_article="# Hello\nTranslated content.",
            source_lang="中文",
            target_lang="英文",
        )
        assert resp.translated_article == "# Hello\nTranslated content."
        assert resp.source_lang == "中文"
        assert resp.target_lang == "英文"

    def test_missing_translated_article_rejected(self):
        """缺少 translated_article 应报错"""
        with pytest.raises(ValidationError):
            self.Model(source_lang="中文", target_lang="英文")

    def test_missing_source_lang_rejected(self):
        """缺少 source_lang 应报错"""
        with pytest.raises(ValidationError):
            self.Model(translated_article="# Hello", target_lang="英文")

    def test_missing_target_lang_rejected(self):
        """缺少 target_lang 应报错"""
        with pytest.raises(ValidationError):
            self.Model(translated_article="# Hello", source_lang="中文")

    def test_has_all_required_fields(self):
        """响应模型包含 SPEC 要求的所有字段"""
        resp = self.Model(
            translated_article="# Hello",
            source_lang="中文",
            target_lang="英文",
        )
        for field in ("translated_article", "source_lang", "target_lang"):
            assert hasattr(resp, field), f"缺少字段: {field}"
