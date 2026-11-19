package harness.l1;

import com.jamesmurty.utils.TestXMLBuilder;
import com.jamesmurty.utils.TestXMLBuilder2;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/**
 * Functional tests: the library's own JUnit suite at the pinned vulnerable
 * commit (TestXMLBuilder and TestXMLBuilder2, both driven by
 * BaseXMLBuilderTests), run against the patched library.
 */
public final class FunctionalTests {
    private FunctionalTests() {
    }

    public static void main(String[] args) {
        final Map<String, String> results = new LinkedHashMap<>();
        JUnitCore core = new JUnitCore();
        core.addListener(new RunListener() {
            @Override
            public void testStarted(Description d) {
                results.put(d.getDisplayName(), null);
            }

            @Override
            public void testFailure(Failure f) {
                results.put(f.getDescription().getDisplayName(), Json.describe(f.getException()));
            }
        });
        core.run(TestXMLBuilder.class, TestXMLBuilder2.class);
        int passed = 0;
        int failed = 0;
        List<String> rows = new ArrayList<>();
        for (Map.Entry<String, String> e : results.entrySet()) {
            boolean ok = e.getValue() == null;
            if (ok) {
                passed++;
            } else {
                failed++;
            }
            rows.add("{\"name\":" + Json.str(e.getKey()) + ",\"ok\":" + ok + ",\"detail\":" + Json.str(e.getValue()) + "}");
        }
        System.out.println("PARAPET_RESULT {\"check\":\"functional\",\"passed\":" + passed
                + ",\"failed\":" + failed + ",\"tests\":[" + String.join(",", rows) + "]}");
    }
}
