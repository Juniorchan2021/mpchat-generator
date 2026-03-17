/**
 * 翻译工具函数
 *
 * 纯函数，无副作用，便于单元测试。
 * 供 WorkspaceClient 和 ExternalClient 共享使用。
 */

export interface TranslateTarget {
  lang: string;
  labelKey: string;
}

/**
 * 通过字符比例 + 繁体特征字符检测文章源语言。
 *
 * 判断逻辑：
 * 1. 汉字数量 > 英文单词数 × 0.5  → 中文系
 *    - 含繁体特征字符（體/國/學/說/時等）→ 繁体中文
 *    - 否则                              → 简体中文
 * 2. 否则                          → 英文
 */
export function detectSourceLang(
  text: string,
  stats: { cn: number; en: number },
): string {
  if (stats.cn > stats.en * 0.5) {
    // 覆盖繁体常见高频字（与简体字形不同）
    const traditionalPattern =
      /[\u9ad4\u570b\u5b78\u8aaa\u6642\u9019\u5011\u70ba\u4f86\u9ebc\u96fb\u8eca\u958b\u6771\u897f\u5c08\u6a5f\u5c31\u904e\u9032]/;
    return traditionalPattern.test(text)
      ? "繁体中文 (Traditional Chinese)"
      : "中文 (Chinese)";
  }
  return "英文 (English)";
}

/**
 * 根据源语言返回翻译目标按钮列表。
 *
 * 映射规则：
 * - 中文 (Chinese)                → [英文, 繁体中文]
 * - 英文 (English)                → [简体中文, 繁体中文]
 * - 繁体中文 (Traditional Chinese) → [简体中文, 英文]
 * - 其他（工作台 16 种语言中的其余 13 种）→ [简体中文, 英文]
 */
export function getTranslateTargets(sourceLang: string): TranslateTarget[] {
  switch (sourceLang) {
    case "英文 (English)":
      return [
        { lang: "中文 (Chinese)", labelKey: "btn.translateToZh" },
        { lang: "繁体中文 (Traditional Chinese)", labelKey: "btn.translateToTw" },
      ];
    case "繁体中文 (Traditional Chinese)":
      return [
        { lang: "中文 (Chinese)", labelKey: "btn.translateToZh" },
        { lang: "英文 (English)", labelKey: "btn.translateToEn" },
      ];
    case "中文 (Chinese)":
    case "":
      return [
        { lang: "英文 (English)", labelKey: "btn.translateToEn" },
        { lang: "繁体中文 (Traditional Chinese)", labelKey: "btn.translateToTw" },
      ];
    default:
      // 工作台其他 13 种语言（日/韩/越/泰等）
      return [
        { lang: "中文 (Chinese)", labelKey: "btn.translateToZh" },
        { lang: "英文 (English)", labelKey: "btn.translateToEn" },
      ];
  }
}
