"""
Tests for core/intercom_qa.py

测试策略：
- build_qa_generation_prompt() 纯单元测试（无需 LLM 调用）
- parse_qa_pairs() 纯单元测试（向后兼容）
- parse_qa_result() 纯单元测试（多语言解析）
- plaintext_to_html() 纯单元测试
- generate_qa_pairs() 使用 mock patch call_llm
- upload_to_intercom() 使用 mock patch requests.post
"""
import json
import pytest
from unittest.mock import patch, MagicMock


# ──────────────────────────────────────────────
# build_qa_generation_prompt() 单元测试
# ──────────────────────────────────────────────

class TestBuildQAGenerationPrompt:
    def setup_method(self):
        from core.intercom_qa import build_qa_generation_prompt
        self.build = build_qa_generation_prompt

    def test_returns_two_messages(self):
        """必须返回包含 system + user 两条消息的列表"""
        messages = self.build("发送加密货币", "MPChat", "friendly", 5)
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_feature_description_in_user_message(self):
        """功能描述必须出现在 user 消息中"""
        desc = "用户可以发送和接收稳定币 USDC"
        messages = self.build(desc, "MPChat", "friendly", 5)
        assert desc in messages[1]["content"]

    def test_product_name_in_prompt(self):
        """产品名称必须出现在提示词中"""
        messages = self.build("send payment", "TestApp", "friendly", 5)
        full = messages[0]["content"] + messages[1]["content"]
        assert "TestApp" in full

    def test_count_in_prompt(self):
        """生成数量必须出现在提示词中"""
        messages = self.build("send payment", "MPChat", "friendly", 10)
        full = messages[0]["content"] + messages[1]["content"]
        assert "10" in full

    def test_json_output_required(self):
        """System prompt 必须要求输出 JSON"""
        messages = self.build("send payment", "MPChat", "friendly", 5)
        system = messages[0]["content"]
        assert "JSON" in system or "json" in system

    def test_required_fields_in_prompt(self):
        """提示词必须包含 question / answer / category 字段要求"""
        messages = self.build("send payment", "MPChat", "friendly", 5)
        full = messages[0]["content"] + messages[1]["content"]
        assert "question" in full
        assert "answer" in full
        assert "category" in full

    def test_all_three_languages_in_prompt(self):
        """默认提示词必须包含三个语言 key"""
        messages = self.build("send payment", "MPChat", "friendly", 5)
        full = messages[0]["content"] + messages[1]["content"]
        assert "zh" in full
        assert "zh-TW" in full
        assert "en" in full

    def test_custom_languages_in_prompt(self):
        """自定义语言列表必须反映在提示词中"""
        messages = self.build("send payment", "MPChat", "friendly", 5, languages=["zh", "en"])
        full = messages[0]["content"] + messages[1]["content"]
        assert "zh" in full
        assert "en" in full

    def test_plain_text_answer_required(self):
        """System prompt 必须要求纯文本答案（不含 HTML）"""
        messages = self.build("send payment", "MPChat", "friendly", 5)
        system = messages[0]["content"]
        assert "plain text" in system.lower() or "no html" in system.lower() or "HTML" in system

    def test_empty_feature_description_raises(self):
        """空功能描述应抛出 ValueError"""
        with pytest.raises(ValueError, match="feature_description"):
            self.build("", "MPChat", "friendly", 5)

    def test_whitespace_only_feature_description_raises(self):
        """纯空白描述应抛出 ValueError"""
        with pytest.raises(ValueError, match="feature_description"):
            self.build("   \n\t  ", "MPChat", "friendly", 5)

    def test_count_zero_raises(self):
        """count=0 应抛出 ValueError"""
        with pytest.raises(ValueError, match="count"):
            self.build("send payment", "MPChat", "friendly", 0)

    def test_count_negative_raises(self):
        """count 负数应抛出 ValueError"""
        with pytest.raises(ValueError, match="count"):
            self.build("send payment", "MPChat", "friendly", -1)

    def test_count_over_max_raises(self):
        """count 超过最大值应抛出 ValueError"""
        with pytest.raises(ValueError, match="count"):
            self.build("send payment", "MPChat", "friendly", 51)

    def test_message_contents_are_strings(self):
        """所有消息的 content 字段必须是非空字符串"""
        messages = self.build("send payment", "MPChat", "friendly", 5)
        for msg in messages:
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0

    def test_default_product_name(self):
        """product_name 默认值不影响生成"""
        messages = self.build("send payment", "", "friendly", 5)
        assert isinstance(messages, list)
        assert len(messages) == 2


# ──────────────────────────────────────────────
# parse_qa_pairs() 单元测试（向后兼容）
# ──────────────────────────────────────────────

SAMPLE_QA_JSON = json.dumps([
    {"question": "How do I send USDC?", "answer": "Open MPChat and tap Send.", "category": "Payments"},
    {"question": "What is MPChat?", "answer": "MPChat is a crypto wallet.", "category": "General"},
])


class TestParseQAPairs:
    def setup_method(self):
        from core.intercom_qa import parse_qa_pairs
        self.parse = parse_qa_pairs

    def test_parses_valid_json_array(self):
        """有效 JSON 数组应成功解析"""
        result = self.parse(SAMPLE_QA_JSON)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_result_has_required_fields(self):
        """每个条目必须含 question / answer / category"""
        result = self.parse(SAMPLE_QA_JSON)
        for item in result:
            assert "question" in item
            assert "answer" in item
            assert "category" in item

    def test_strips_code_fences(self):
        """应自动剥离 ```json ... ``` 包裹"""
        wrapped = f"```json\n{SAMPLE_QA_JSON}\n```"
        result = self.parse(wrapped)
        assert len(result) == 2

    def test_strips_plain_code_fences(self):
        """应自动剥离 ``` ... ``` 包裹"""
        wrapped = f"```\n{SAMPLE_QA_JSON}\n```"
        result = self.parse(wrapped)
        assert len(result) == 2

    def test_extracts_array_from_mixed_text(self):
        """应从混合文本中提取 JSON 数组"""
        text = f"Here are the QA pairs:\n{SAMPLE_QA_JSON}\nDone."
        result = self.parse(text)
        assert len(result) == 2

    def test_empty_string_returns_empty_list(self):
        """空字符串应返回空列表"""
        result = self.parse("")
        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        """纯空白应返回空列表"""
        result = self.parse("   \n  ")
        assert result == []

    def test_invalid_json_returns_empty_list(self):
        """无效 JSON 应返回空列表，不抛出异常"""
        result = self.parse("not json at all")
        assert result == []

    def test_missing_fields_are_filled_with_defaults(self):
        """缺失字段应用默认值填充"""
        partial = json.dumps([{"question": "How?"}])
        result = self.parse(partial)
        assert len(result) == 1
        assert result[0]["answer"] == ""
        assert result[0]["category"] == "General"

    def test_non_list_json_returns_empty(self):
        """非数组 JSON（对象）应返回空列表"""
        result = self.parse('{"question": "test"}')
        assert result == []

    def test_non_dict_items_are_skipped(self):
        """数组中的非对象条目应被过滤"""
        mixed = json.dumps(["string", 42, {"question": "Q?", "answer": "A.", "category": "Test"}])
        result = self.parse(mixed)
        assert len(result) == 1


# ──────────────────────────────────────────────
# parse_qa_result() 多语言解析单元测试
# ──────────────────────────────────────────────

SAMPLE_MULTILANG = json.dumps({
    "zh": [
        {"question": "如何发送 USDC？", "answer": "打开 MPChat，点击发送按钮。", "category": "Payments"},
    ],
    "zh-TW": [
        {"question": "如何傳送 USDC？", "answer": "開啟 MPChat，點擊傳送按鈕。", "category": "Payments"},
    ],
    "en": [
        {"question": "How do I send USDC?", "answer": "Open MPChat and tap Send.", "category": "Payments"},
    ],
})

LANGUAGES = ["zh", "zh-TW", "en"]


class TestParseQAResult:
    def setup_method(self):
        from core.intercom_qa import parse_qa_result
        self.parse = parse_qa_result

    def test_parses_valid_multilang_json(self):
        """有效多语言 JSON 应成功解析所有语言"""
        result = self.parse(SAMPLE_MULTILANG, LANGUAGES)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(LANGUAGES)

    def test_each_language_returns_list(self):
        """每个语言对应的值必须是列表"""
        result = self.parse(SAMPLE_MULTILANG, LANGUAGES)
        for lang in LANGUAGES:
            assert isinstance(result[lang], list)

    def test_each_qa_has_required_fields(self):
        """每个 QA 对必须含 question / answer / category"""
        result = self.parse(SAMPLE_MULTILANG, LANGUAGES)
        for lang in LANGUAGES:
            for item in result[lang]:
                assert "question" in item
                assert "answer" in item
                assert "category" in item

    def test_strips_code_fences(self):
        """应自动剥离 ```json ... ``` 包裹"""
        wrapped = f"```json\n{SAMPLE_MULTILANG}\n```"
        result = self.parse(wrapped, LANGUAGES)
        assert len(result["zh"]) == 1

    def test_empty_string_returns_empty_per_language(self):
        """空字符串应为每个语言返回空列表"""
        result = self.parse("", LANGUAGES)
        for lang in LANGUAGES:
            assert result[lang] == []

    def test_invalid_json_returns_empty_per_language(self):
        """无效 JSON 应为每个语言返回空列表，不抛出异常"""
        result = self.parse("not json", LANGUAGES)
        for lang in LANGUAGES:
            assert result[lang] == []

    def test_missing_language_key_returns_empty_list(self):
        """缺少某个语言 key 时该语言应返回空列表"""
        partial = json.dumps({"zh": [{"question": "Q?", "answer": "A.", "category": "Test"}]})
        result = self.parse(partial, LANGUAGES)
        assert len(result["zh"]) == 1
        assert result["zh-TW"] == []
        assert result["en"] == []

    def test_custom_language_list(self):
        """自定义语言列表只处理指定语言"""
        result = self.parse(SAMPLE_MULTILANG, ["zh", "en"])
        assert set(result.keys()) == {"zh", "en"}

    def test_extracts_object_from_mixed_text(self):
        """应从混合文本中提取 JSON 对象"""
        text = f"Here are the results:\n{SAMPLE_MULTILANG}\nEnd."
        result = self.parse(text, LANGUAGES)
        assert len(result["zh"]) == 1


# ──────────────────────────────────────────────
# plaintext_to_html() 单元测试
# ──────────────────────────────────────────────

class TestPlaintextToHtml:
    def setup_method(self):
        from core.intercom_qa import plaintext_to_html
        self.convert = plaintext_to_html

    def test_plain_paragraph(self):
        """普通段落应包装为 <p>"""
        result = self.convert("This is a paragraph.")
        assert result == "<p>This is a paragraph.</p>"

    def test_unordered_list(self):
        """以 - 开头的行应转换为 <ul><li>"""
        result = self.convert("- Item 1\n- Item 2")
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result

    def test_asterisk_list(self):
        """以 * 开头的行应转换为 <ul><li>"""
        result = self.convert("* Item A\n* Item B")
        assert "<ul>" in result
        assert "<li>Item A</li>" in result

    def test_ordered_list(self):
        """以数字点开头的行应转换为 <ol><li>"""
        result = self.convert("1. First\n2. Second")
        assert "<ol>" in result
        assert "<li>First</li>" in result
        assert "<li>Second</li>" in result

    def test_mixed_content(self):
        """混合段落和列表应正确处理"""
        text = "Introduction.\n\n- Step 1\n- Step 2\n\nConclusion."
        result = self.convert(text)
        assert "<p>Introduction.</p>" in result
        assert "<ul>" in result
        assert "<p>Conclusion.</p>" in result

    def test_already_html_passthrough(self):
        """已含 HTML 标签的内容应直接返回，不双重转换"""
        html = "<p>Already HTML content.</p>"
        result = self.convert(html)
        assert result == html

    def test_empty_string_returns_empty(self):
        """空字符串应返回空字符串"""
        result = self.convert("")
        assert result == ""

    def test_whitespace_only_returns_empty(self):
        """纯空白应返回空字符串"""
        result = self.convert("   \n  ")
        assert result == ""

    def test_chinese_paragraph(self):
        """中文段落应正确包装"""
        result = self.convert("打开 MPChat，点击发送按钮。")
        assert "<p>打开 MPChat，点击发送按钮。</p>" in result

    def test_chinese_list(self):
        """中文列表项应正确转换"""
        result = self.convert("- 打开应用\n- 点击发送")
        assert "<li>打开应用</li>" in result


# ──────────────────────────────────────────────
# generate_qa_pairs() 集成测试（mock call_llm）
# ──────────────────────────────────────────────

class TestGenerateQAPairs:
    def setup_method(self):
        from core.intercom_qa import generate_qa_pairs
        self.generate = generate_qa_pairs

    @patch("core.intercom_qa.call_llm")
    def test_returns_dict(self, mock_llm):
        """正常调用应返回字典"""
        mock_llm.return_value = SAMPLE_MULTILANG
        result = self.generate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
        )
        assert isinstance(result, dict)

    @patch("core.intercom_qa.call_llm")
    def test_returns_all_default_languages(self, mock_llm):
        """默认调用应包含 zh / zh-TW / en 三个 key"""
        mock_llm.return_value = SAMPLE_MULTILANG
        result = self.generate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
        )
        assert "zh" in result
        assert "zh-TW" in result
        assert "en" in result

    @patch("core.intercom_qa.call_llm")
    def test_call_llm_invoked_once(self, mock_llm):
        """call_llm 应仅被调用一次"""
        mock_llm.return_value = SAMPLE_MULTILANG
        self.generate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
        )
        mock_llm.assert_called_once()

    @patch("core.intercom_qa.call_llm")
    def test_correct_provider_passed(self, mock_llm):
        """call_llm 应使用传入的 provider"""
        mock_llm.return_value = SAMPLE_MULTILANG
        self.generate(
            provider="anthropic",
            api_key="sk-ant-test",
            base_url="",
            model="claude-opus-4-5",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
        )
        call_kwargs = mock_llm.call_args
        assert (
            call_kwargs.kwargs.get("provider") == "anthropic"
            or call_kwargs.args[0] == "anthropic"
        )

    def test_empty_api_key_raises(self):
        """空 api_key 应在调用 LLM 前抛出 ValueError"""
        with pytest.raises(ValueError, match="api_key"):
            self.generate(
                provider="openai",
                api_key="",
                base_url="",
                model="gpt-4o",
                feature_description="send USDC",
                product_name="MPChat",
                tone="friendly",
                count=5,
            )

    def test_empty_feature_description_raises(self):
        """空功能描述应在调用 LLM 前抛出 ValueError"""
        with pytest.raises(ValueError):
            self.generate(
                provider="openai",
                api_key="sk-test",
                base_url="",
                model="gpt-4o",
                feature_description="",
                product_name="MPChat",
                tone="friendly",
                count=5,
            )

    @patch("core.intercom_qa.call_llm")
    def test_llm_returns_empty_gives_empty_dict(self, mock_llm):
        """LLM 返回空字符串时应返回每个语言均为空列表的字典"""
        mock_llm.return_value = ""
        result = self.generate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
        )
        assert isinstance(result, dict)
        for lang in ["zh", "zh-TW", "en"]:
            assert result[lang] == []

    @patch("core.intercom_qa.call_llm")
    def test_custom_languages_respected(self, mock_llm):
        """自定义语言列表应传递给解析函数"""
        two_lang = json.dumps({"zh": [], "en": []})
        mock_llm.return_value = two_lang
        result = self.generate(
            provider="openai",
            api_key="sk-test",
            base_url="",
            model="gpt-4o",
            feature_description="send USDC",
            product_name="MPChat",
            tone="friendly",
            count=5,
            languages=["zh", "en"],
        )
        assert set(result.keys()) == {"zh", "en"}


# ──────────────────────────────────────────────
# upload_to_intercom() 单元测试（mock requests）
# ──────────────────────────────────────────────

class TestUploadToIntercom:
    def setup_method(self):
        from core.intercom_qa import upload_to_intercom
        self.upload = upload_to_intercom

    @patch("core.intercom_qa.requests.post")
    def test_success_returns_article_id(self, mock_post):
        """成功上传应返回包含 id 的字典"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "12345", "title": "Test Article"}
        mock_post.return_value = mock_resp

        result = self.upload(
            token="intercom-token",
            collection_id="col-123",
            title="How to send USDC?",
            body="Open MPChat and tap Send.",
        )
        assert "id" in result
        assert result["id"] == "12345"

    @patch("core.intercom_qa.requests.post")
    def test_posts_to_correct_endpoint(self, mock_post):
        """应调用 Intercom Help Center Articles API"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "abc"}
        mock_post.return_value = mock_resp

        self.upload(
            token="tok",
            collection_id="col",
            title="Title",
            body="Body content.",
        )
        called_url = mock_post.call_args[0][0] if mock_post.call_args[0] else mock_post.call_args[1].get("url", "")
        assert "intercom" in called_url.lower() or "articles" in called_url.lower()

    @patch("core.intercom_qa.requests.post")
    def test_auth_header_contains_token(self, mock_post):
        """请求必须在 Authorization header 中包含 token"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "x"}
        mock_post.return_value = mock_resp

        self.upload(
            token="my-secret-token",
            collection_id="col",
            title="Title",
            body="Body content.",
        )
        call_kwargs = mock_post.call_args
        headers = call_kwargs[1].get("headers", {}) if call_kwargs[1] else {}
        auth = headers.get("Authorization", "")
        assert "my-secret-token" in auth

    @patch("core.intercom_qa.requests.post")
    def test_locale_included_in_payload(self, mock_post):
        """locale 参数应包含在请求 payload 中"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "y"}
        mock_post.return_value = mock_resp

        self.upload(
            token="tok",
            collection_id="col",
            title="Title",
            body="Body.",
            locale="zh-TW",
        )
        sent_payload = mock_post.call_args[1].get("json", {})
        assert sent_payload.get("locale") == "zh-TW"

    @patch("core.intercom_qa.requests.post")
    def test_plaintext_body_converted_to_html(self, mock_post):
        """纯文本 body 应在上传前转换为 HTML"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "z"}
        mock_post.return_value = mock_resp

        self.upload(
            token="tok",
            collection_id="col",
            title="Title",
            body="Plain text paragraph.",
        )
        sent_payload = mock_post.call_args[1].get("json", {})
        assert "<p>" in sent_payload.get("body", "")

    @patch("core.intercom_qa.requests.post")
    def test_non_200_response_raises(self, mock_post):
        """非 200 响应应抛出异常"""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        mock_post.return_value = mock_resp

        with pytest.raises(Exception):
            self.upload(
                token="bad-token",
                collection_id="col",
                title="Title",
                body="Body.",
            )

    def test_empty_token_raises(self):
        """空 token 应抛出 ValueError"""
        with pytest.raises(ValueError, match="token"):
            self.upload(
                token="",
                collection_id="col",
                title="Title",
                body="Body.",
            )

    def test_empty_title_raises(self):
        """空 title 应抛出 ValueError"""
        with pytest.raises(ValueError, match="title"):
            self.upload(
                token="tok",
                collection_id="col",
                title="",
                body="Body.",
            )

    def test_empty_body_raises(self):
        """空 body 应抛出 ValueError"""
        with pytest.raises(ValueError, match="body"):
            self.upload(
                token="tok",
                collection_id="col",
                title="Title",
                body="",
            )


# ──────────────────────────────────────────────
# fetch_intercom_collections() 单元测试
# ──────────────────────────────────────────────

class TestFetchIntercomCollections:
    def setup_method(self):
        from core.intercom_qa import fetch_intercom_collections
        self.fetch = fetch_intercom_collections

    SAMPLE_RESPONSE = {
        "type": "list",
        "data": [
            {
                "id": 12345,
                "name": "Getting Started",
                "translated_content": {
                    "zh": {"name": "快速开始", "type": "collection_translated_content"},
                    "en": {"name": "Getting Started", "type": "collection_translated_content"},
                },
            },
            {
                "id": 67890,
                "name": "Payments",
                "translated_content": {
                    "en": {"name": "Payments", "type": "collection_translated_content"},
                },
            },
        ],
    }

    @patch("core.intercom_qa.requests.get")
    def test_returns_list(self, mock_get):
        """成功响应应返回列表"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = self.fetch("valid-token")
        assert isinstance(result, list)
        assert len(result) == 2

    @patch("core.intercom_qa.requests.get")
    def test_normalizes_id_to_string(self, mock_get):
        """id 应规范化为字符串"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = self.fetch("valid-token")
        assert result[0]["id"] == "12345"

    @patch("core.intercom_qa.requests.get")
    def test_extracts_translated_content(self, mock_get):
        """translated_content 应提取为 {locale: name_str} 字典"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = self.fetch("valid-token")
        tc = result[0]["translated_content"]
        assert tc["zh"] == "快速开始"
        assert tc["en"] == "Getting Started"

    @patch("core.intercom_qa.requests.get")
    def test_auth_header_set(self, mock_get):
        """Authorization header 应包含 token"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        mock_get.return_value = mock_resp

        self.fetch("my-token")
        headers = mock_get.call_args[1].get("headers", {})
        assert "my-token" in headers.get("Authorization", "")

    @patch("core.intercom_qa.requests.get")
    def test_non_200_raises(self, mock_get):
        """非 200 响应应抛出异常"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        with pytest.raises(Exception):
            self.fetch("bad-token")

    def test_empty_token_raises(self):
        """空 token 应抛出 ValueError"""
        with pytest.raises(ValueError, match="token"):
            self.fetch("")

    @patch("core.intercom_qa.requests.get")
    def test_empty_data_returns_empty_list(self, mock_get):
        """data 为空时应返回空列表"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        mock_get.return_value = mock_resp

        result = self.fetch("tok")
        assert result == []
