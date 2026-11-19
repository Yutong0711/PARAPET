package harness.c1;

import example.prefs.PrefsCodec.UserPrefs;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Deterministic legitimate preference values used by tests, probes, and the workload. */
final class Samples {
    private Samples() {
    }

    static List<String> files(int n, String prefix) {
        List<String> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(prefix + String.format("%04d", i) + ".java");
        }
        return out;
    }

    static Map<String, String> shortcuts(int n) {
        Map<String, String> out = new LinkedHashMap<>();
        for (int i = 0; i < n; i++) {
            out.put("ctrl+alt+" + (char) ('a' + (i % 26)) + i, "action.command." + i);
        }
        return out;
    }

    static UserPrefs typical() {
        return new UserPrefs("user-0042", "solarized-dark", 14,
                files(20, "/home/user-0042/projects/app/src/main/java/com/example/File"),
                shortcuts(12));
    }

    static UserPrefs empty() {
        return new UserPrefs("", null, 0, new ArrayList<>(), new LinkedHashMap<>());
    }

    static UserPrefs large() {
        return new UserPrefs("user-large", "light", 11,
                files(2000, "/srv/repo/module/src/File"), shortcuts(200));
    }

    static UserPrefs unicode() {
        Map<String, String> sc = new LinkedHashMap<>();
        sc.put("\u2318+\u00e9", "\u4fdd\u5b58");
        sc.put("ctrl+\u00df", "\u043e\u0442\u043a\u0440\u044b\u0442\u044c");
        List<String> files = new ArrayList<>();
        files.add("/home/zo\u00eb/\u043f\u0440\u043e\u0435\u043a\u0442/\u0444\u0430\u0439\u043b.txt");
        files.add("C:\\Users\\\u738b\u5c0f\u660e\\\u6587\u6863\\\u62a5\u544a.md");
        files.add("/tmp/rocket-\uD83D\uDE80.txt");
        return new UserPrefs("Zo\u00eb \u738b\u5c0f\u660e \uD83D\uDE80", "nuit-\u00e9toil\u00e9e", 13, files, sc);
    }

    /** Canonical text form of a decoded value, built only from the public getters. */
    static String canonical(UserPrefs p) {
        StringBuilder b = new StringBuilder();
        b.append(p.getUser()).append('\u0000').append(p.getTheme()).append('\u0000')
                .append(p.getFontSize()).append('\u0000');
        for (String f : p.getRecentFiles()) {
            b.append(f).append('\u0001');
        }
        b.append('\u0000');
        for (Map.Entry<String, String> e : p.getShortcuts().entrySet()) {
            b.append(e.getKey()).append('=').append(e.getValue()).append('\u0001');
        }
        return b.toString();
    }
}
