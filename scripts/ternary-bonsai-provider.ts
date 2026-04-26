/**
 * Ternary Bonsai Provider Extension
 * 
 * Local llama.cpp server running on RTX 2080 SUPER
 * 
 * Usage:
 *   pi -e ~/ternary-bonsai-provider.ts
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
    pi.registerProvider("ternary-bonsai", {
        baseUrl: "http://localhost:8080/v1",
        apiKey: "none", // No API key needed for local server
        api: "openai-completions",
        
        models: [
            {
                id: "Ternary-Bonsai",
                name: "Ternary Bonsai 8B",
                reasoning: false,
                input: ["text"],
                cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
                contextWindow: 65536,
                maxTokens: 4096,
                compat: {
                    supportsDeveloperRole: false,
                    requiresToolResultName: true,
                    thinkingFormat: "qwen-chat-template",
                }
            }
        ]
    });
}
