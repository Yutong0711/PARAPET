package harness.c2;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.stream.Stream;

/**
 * Harmless canary for XML external entity checks: a marker file in a fresh
 * temporary directory. If the marker text shows up in what the loader returns
 * (or in its error message), the parser read a local file named by the input.
 * Nothing leaves the machine and no network URL is ever used.
 */
final class CanaryFiles implements AutoCloseable {
    static final String MARKER = "PARAPET-CANARY-C2-5b1e";

    final Path dir;
    final Path secret;

    CanaryFiles() throws IOException {
        dir = Files.createTempDirectory("parapet-c2-");
        secret = dir.resolve("secret.txt");
        Files.write(secret, MARKER.getBytes(StandardCharsets.US_ASCII));
    }

    String secretUri() {
        return secret.toUri().toString();
    }

    String writeFile(String name, String content) throws IOException {
        Path p = dir.resolve(name);
        Files.write(p, content.getBytes(StandardCharsets.UTF_8));
        return p.toUri().toString();
    }

    @Override
    public void close() throws IOException {
        try (Stream<Path> walk = Files.walk(dir)) {
            walk.sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
        }
    }
}
