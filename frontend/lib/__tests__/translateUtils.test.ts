import { describe, it, expect } from "vitest";
import { detectSourceLang, getTranslateTargets } from "../translateUtils";

// ─── detectSourceLang ──────────────────────────────────────────────────────

describe("detectSourceLang", () => {
  // ── 简体中文 ───────────────────────────────────────────────────────────

  it("纯简体中文文本 → 中文 (Chinese)", () => {
    const text = "这是一篇关于加密货币支付的文章，介绍了最新的支付技术。";
    const stats = { cn: text.match(/[\u4e00-\u9fff]/g)!.length, en: 0 };
    expect(detectSourceLang(text, stats)).toBe("中文 (Chinese)");
  });

  it("中英混排但以中文为主 → 中文 (Chinese)", () => {
    const text = "MPChat 是一款支持 USDT 支付的应用，可以订阅 ChatGPT Plus。";
    const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const en = (text.match(/[a-zA-Z]+/g) || []).length;
    expect(detectSourceLang(text, { cn, en })).toBe("中文 (Chinese)");
  });

  it("stats.cn 为 0，stats.en > 0 → 英文 (English)", () => {
    const text = "This is an article about crypto payment.";
    expect(detectSourceLang(text, { cn: 0, en: 7 })).toBe("英文 (English)");
  });

  // ── 英文 ────────────────────────────────────────────────────────────────

  it("纯英文文本 → 英文 (English)", () => {
    const text = "Crypto payments are transforming e-commerce worldwide.";
    const stats = { cn: 0, en: (text.match(/[a-zA-Z]+/g) || []).length };
    expect(detectSourceLang(text, stats)).toBe("英文 (English)");
  });

  it("英文为主、含少量汉字 → 英文 (English)", () => {
    // cn=2, en=20: 2 <= 20*0.5=10，判为英文
    expect(detectSourceLang("some text 文章", { cn: 2, en: 20 })).toBe("英文 (English)");
  });

  it("空文本（stats 全 0）→ 英文 (English)", () => {
    expect(detectSourceLang("", { cn: 0, en: 0 })).toBe("英文 (English)");
  });

  // ── 繁体中文 ────────────────────────────────────────────────────────────

  it("含繁体特征字 體 → 繁体中文 (Traditional Chinese)", () => {
    const text = "這是一篇關於加密貨幣支付的文章，介紹了最新的支付技術體系。";
    const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    expect(detectSourceLang(text, { cn, en: 0 })).toBe("繁体中文 (Traditional Chinese)");
  });

  it("含繁体特征字 國 → 繁体中文 (Traditional Chinese)", () => {
    const text = "台灣是亞洲最重要的科技國家之一，影響全球產業。";
    const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    expect(detectSourceLang(text, { cn, en: 0 })).toBe("繁体中文 (Traditional Chinese)");
  });

  it("含繁体特征字 說/時/這 → 繁体中文 (Traditional Chinese)", () => {
    const text = "他說這個時候應該進行更多投資。";
    const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    expect(detectSourceLang(text, { cn, en: 0 })).toBe("繁体中文 (Traditional Chinese)");
  });

  it("无繁体特征字的中文文本不应误判为繁体", () => {
    // 这些常用简体字不在繁体特征字集合内
    const text = "今天天气很好，我们一起去公园散步吧。";
    const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    expect(detectSourceLang(text, { cn, en: 0 })).toBe("中文 (Chinese)");
  });

  // ── 边界值 ──────────────────────────────────────────────────────────────

  it("cn 恰好等于 en * 0.5 时（不大于）→ 英文 (English)", () => {
    // cn=5, en=10: 5 > 5 为 false → 英文
    expect(detectSourceLang("text", { cn: 5, en: 10 })).toBe("英文 (English)");
  });

  it("cn 恰好大于 en * 0.5 时 → 中文判断分支", () => {
    // cn=6, en=10: 6 > 5 → 进入中文分支（无繁体字 → 简体）
    expect(detectSourceLang("普通汉字文本", { cn: 6, en: 10 })).toBe("中文 (Chinese)");
  });
});

// ─── getTranslateTargets ───────────────────────────────────────────────────

describe("getTranslateTargets", () => {
  // ── 简体中文源 ──────────────────────────────────────────────────────────

  it("源语言为简体中文 → 目标为英文 + 繁体中文", () => {
    const targets = getTranslateTargets("中文 (Chinese)");
    expect(targets).toHaveLength(2);
    expect(targets[0].lang).toBe("英文 (English)");
    expect(targets[0].labelKey).toBe("btn.translateToEn");
    expect(targets[1].lang).toBe("繁体中文 (Traditional Chinese)");
    expect(targets[1].labelKey).toBe("btn.translateToTw");
  });

  it("源语言为空字符串（默认）→ 同简体中文，目标为英文 + 繁体中文", () => {
    const targets = getTranslateTargets("");
    expect(targets[0].lang).toBe("英文 (English)");
    expect(targets[1].lang).toBe("繁体中文 (Traditional Chinese)");
  });

  // ── 英文源 ─────────────────────────────────────────────────────────────

  it("源语言为英文 → 目标为简体中文 + 繁体中文", () => {
    const targets = getTranslateTargets("英文 (English)");
    expect(targets).toHaveLength(2);
    expect(targets[0].lang).toBe("中文 (Chinese)");
    expect(targets[0].labelKey).toBe("btn.translateToZh");
    expect(targets[1].lang).toBe("繁体中文 (Traditional Chinese)");
    expect(targets[1].labelKey).toBe("btn.translateToTw");
  });

  // ── 繁体中文源 ──────────────────────────────────────────────────────────

  it("源语言为繁体中文 → 目标为简体中文 + 英文", () => {
    const targets = getTranslateTargets("繁体中文 (Traditional Chinese)");
    expect(targets).toHaveLength(2);
    expect(targets[0].lang).toBe("中文 (Chinese)");
    expect(targets[0].labelKey).toBe("btn.translateToZh");
    expect(targets[1].lang).toBe("英文 (English)");
    expect(targets[1].labelKey).toBe("btn.translateToEn");
  });

  // ── 工作台其他语言源 ────────────────────────────────────────────────────

  it("源语言为日语 → 目标为简体中文 + 英文", () => {
    const targets = getTranslateTargets("日本語 (Japanese)");
    expect(targets[0].lang).toBe("中文 (Chinese)");
    expect(targets[1].lang).toBe("英文 (English)");
  });

  it("源语言为韩语 → 目标为简体中文 + 英文", () => {
    const targets = getTranslateTargets("한국어 (Korean)");
    expect(targets[0].labelKey).toBe("btn.translateToZh");
    expect(targets[1].labelKey).toBe("btn.translateToEn");
  });

  it("源语言为阿拉伯语 → 目标为简体中文 + 英文", () => {
    const targets = getTranslateTargets("العربية (Arabic)");
    expect(targets).toHaveLength(2);
    expect(targets[0].lang).toBe("中文 (Chinese)");
    expect(targets[1].lang).toBe("英文 (English)");
  });

  // ── 返回值结构校验 ──────────────────────────────────────────────────────

  it("所有返回目标均包含 lang 和 labelKey 字段", () => {
    const testCases = [
      "中文 (Chinese)",
      "英文 (English)",
      "繁体中文 (Traditional Chinese)",
      "日本語 (Japanese)",
    ];
    for (const lang of testCases) {
      const targets = getTranslateTargets(lang);
      for (const t of targets) {
        expect(t).toHaveProperty("lang");
        expect(t).toHaveProperty("labelKey");
        expect(typeof t.lang).toBe("string");
        expect(typeof t.labelKey).toBe("string");
      }
    }
  });

  it("目标语言中不包含源语言本身", () => {
    const cases: [string, string][] = [
      ["中文 (Chinese)", "中文 (Chinese)"],
      ["英文 (English)", "英文 (English)"],
      ["繁体中文 (Traditional Chinese)", "繁体中文 (Traditional Chinese)"],
    ];
    for (const [source, sourceLang] of cases) {
      const targets = getTranslateTargets(source);
      const langs = targets.map((t) => t.lang);
      expect(langs).not.toContain(sourceLang);
    }
  });
});
