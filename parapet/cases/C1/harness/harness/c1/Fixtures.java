package harness.c1;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/** Reads pre-built payload and probe tokens from the case fixtures directory. */
final class Fixtures {
    private Fixtures() {
    }

    static Path dir() {
        String d = System.getProperty("parapet.fixtures");
        if (d == null) {
            throw new IllegalStateException("system property parapet.fixtures is not set");
        }
        return Paths.get(d);
    }

    static String read(String name) throws IOException {
        return new String(Files.readAllBytes(dir().resolve(name)), StandardCharsets.US_ASCII).trim();
    }
}
