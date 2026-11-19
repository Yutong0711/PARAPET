package harness.c1;

import example.prefs.PrefsCodec;
import example.prefs.PrefsCodec.UserPrefs;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Functional tests: the behavior a fix must preserve. They exercise the public
 * API only (encode/decode round trips and UserPrefs accessors), so they apply
 * to any wire format. Compatibility with tokens written by the original
 * implementation is NOT required here; it is reported separately by Probes.
 */
public final class FunctionalTests {
    interface Body {
        void run() throws Exception;
    }

    private static final List<String> RESULTS = new ArrayList<>();
    private static int passed;
    private static int failed;

    private FunctionalTests() {
    }

    static void test(String name, Body body) {
        String detail = null;
        boolean ok;
        try {
            body.run();
            ok = true;
        } catch (Throwable t) {
            ok = false;
            detail = Json.describe(t);
        }
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        RESULTS.add("{\"name\":" + Json.str(name) + ",\"ok\":" + ok + ",\"detail\":" + Json.str(detail) + "}");
    }

    static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    static UserPrefs roundTrip(UserPrefs p) throws Exception {
        return PrefsCodec.decode(PrefsCodec.encode(p));
    }

    static void assertSame(UserPrefs expected, UserPrefs actual) {
        check(actual != null, "decode returned null");
        check(java.util.Objects.equals(expected.getUser(), actual.getUser()), "user differs");
        check(java.util.Objects.equals(expected.getTheme(), actual.getTheme()), "theme differs");
        check(expected.getFontSize() == actual.getFontSize(), "fontSize differs");
        check(expected.getRecentFiles().equals(actual.getRecentFiles()), "recentFiles differ");
        check(expected.getShortcuts().equals(actual.getShortcuts()), "shortcuts differ");
        check(new ArrayList<>(expected.getShortcuts().keySet())
                .equals(new ArrayList<>(actual.getShortcuts().keySet())), "shortcut order differs");
        check(expected.equals(actual), "equals() is false after round trip");
        check(expected.hashCode() == actual.hashCode(), "hashCode differs after round trip");
    }

    static void expectFailure(Body body, String message) {
        boolean threw = false;
        try {
            body.run();
        } catch (Throwable t) {
            threw = true;
        }
        check(threw, message);
    }

    public static void main(String[] args) {
        test("roundtrip_typical", () -> {
            UserPrefs p = Samples.typical();
            assertSame(p, roundTrip(p));
        });
        test("roundtrip_empty_collections", () -> {
            UserPrefs p = Samples.empty();
            assertSame(p, roundTrip(p));
        });
        test("roundtrip_null_theme", () -> {
            UserPrefs p = new UserPrefs("u", null, 12, List.of("/a"), Map.of("k", "v"));
            assertSame(p, roundTrip(p));
        });
        test("roundtrip_unicode", () -> {
            UserPrefs p = Samples.unicode();
            assertSame(p, roundTrip(p));
        });
        test("roundtrip_500_recent_files", () -> {
            UserPrefs p = new UserPrefs("u", "dark", 10, Samples.files(500, "/r/F"), Samples.shortcuts(50));
            assertSame(p, roundTrip(p));
        });
        test("order_preserved", () -> {
            List<String> files = new ArrayList<>(List.of("/z", "/a", "/m", "/a"));
            Map<String, String> sc = new LinkedHashMap<>();
            sc.put("z", "1");
            sc.put("a", "2");
            sc.put("m", "3");
            UserPrefs p = new UserPrefs("u", "t", 9, files, sc);
            assertSame(p, roundTrip(p));
        });
        test("int_extremes", () -> {
            assertSame(new UserPrefs("u", "t", Integer.MAX_VALUE, List.of(), Map.of()),
                    roundTrip(new UserPrefs("u", "t", Integer.MAX_VALUE, List.of(), Map.of())));
            assertSame(new UserPrefs("u", "t", Integer.MIN_VALUE, List.of(), Map.of()),
                    roundTrip(new UserPrefs("u", "t", Integer.MIN_VALUE, List.of(), Map.of())));
        });
        test("token_is_base64_text", () -> {
            String token = PrefsCodec.encode(Samples.typical());
            check(token != null && !token.isEmpty(), "empty token");
            check(token.matches("[A-Za-z0-9+/]*={0,2}"), "token is not standard Base64 text");
        });
        test("decoded_collections_are_read_only", () -> {
            UserPrefs q = roundTrip(Samples.typical());
            expectFailure(() -> q.getRecentFiles().add("/x"), "recentFiles view is mutable");
            expectFailure(() -> q.getShortcuts().put("k", "v"), "shortcuts view is mutable");
        });
        test("decode_rejects_truncated_token", () -> {
            String token = PrefsCodec.encode(Samples.typical());
            String cut = token.substring(0, (token.length() / 2) / 4 * 4);
            expectFailure(() -> PrefsCodec.decode(cut), "truncated token was accepted");
        });
        test("decode_rejects_non_token_text", () -> {
            String junk = Base64.getEncoder().encodeToString(
                    "hello world, this is not a preferences token".getBytes(StandardCharsets.US_ASCII));
            expectFailure(() -> PrefsCodec.decode(junk), "non-token text was accepted");
        });
        System.out.println("PARAPET_RESULT {\"check\":\"functional\",\"passed\":" + passed
                + ",\"failed\":" + failed + ",\"tests\":[" + String.join(",", RESULTS) + "]}");
    }
}
