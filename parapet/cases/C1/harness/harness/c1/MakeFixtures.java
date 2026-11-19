package harness.c1;

import example.prefs.PrefsCodec;
import example.prefs.PrefsCodec.UserPrefs;
import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import thirdparty.canary.GadgetA;
import thirdparty.canary.GadgetB;
import thirdparty.canary.GadgetC;

/**
 * Builds the payload and probe fixtures. Compiled and run ONLY against the
 * original (unpatched) PrefsCodec, once, at case-authoring time; its output
 * is committed under fixtures/. Never compiled against a patch.
 */
public final class MakeFixtures {
    private MakeFixtures() {
    }

    static String serialize(Object o) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(o);
        }
        return Base64.getEncoder().encodeToString(bytes.toByteArray());
    }

    static void setField(Object target, String name, Object value) throws Exception {
        Field f = target.getClass().getDeclaredField(name);
        f.setAccessible(true);
        f.set(target, value);
    }

    static void write(Path dir, String name, String token) throws Exception {
        Files.write(dir.resolve(name), (token + "\n").getBytes(StandardCharsets.US_ASCII));
    }

    public static void main(String[] args) throws Exception {
        Path dir = Paths.get(args[0]);
        Files.createDirectories(dir);

        // Reproducer: a gadget object as the whole token.
        write(dir, "reproducer.b64", serialize(new GadgetA("reproducer")));

        // Held-out 1: a different gadget class, reached through HashMap key rehashing.
        HashMap<Object, String> map = new HashMap<>();
        map.put(new GadgetB("key"), "value");
        write(dir, "heldout1.b64", serialize(map));

        // Held-out 2: a third gadget class nested inside otherwise legitimate preferences.
        UserPrefs nested = Samples.typical();
        List<Object> files = new ArrayList<>();
        files.add("/home/user/notes.txt");
        files.add(new GadgetC(7));
        files.add("/home/user/todo.txt");
        setField(nested, "recentFiles", files);
        write(dir, "heldout2.b64", serialize(nested));

        // Probes: legitimate tokens the original implementation writes or accepts.
        write(dir, "probe_typical.b64", PrefsCodec.encode(Samples.typical()));
        write(dir, "probe_empty.b64", PrefsCodec.encode(Samples.empty()));
        write(dir, "probe_large.b64", PrefsCodec.encode(Samples.large()));
        write(dir, "probe_unicode.b64", PrefsCodec.encode(Samples.unicode()));
        UserPrefs legacyList = Samples.typical();
        setField(legacyList, "recentFiles", new LinkedList<>(legacyList.getRecentFiles()));
        write(dir, "probe_legacy_linkedlist.b64", PrefsCodec.encode(legacyList));
        UserPrefs legacyMap = Samples.typical();
        setField(legacyMap, "shortcuts", new HashMap<>(legacyMap.getShortcuts()));
        write(dir, "probe_legacy_hashmap.b64", PrefsCodec.encode(legacyMap));
    }
}
