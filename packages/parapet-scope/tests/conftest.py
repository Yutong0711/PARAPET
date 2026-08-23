"""Java fixtures small enough to reason about by hand."""

import pytest

BASE = {
    "src/main/java/acme/Loader.java": """
package acme;

import acme.util.Buffer;

/** Loads records. A comment with a { brace and "a string }". */
public class Loader {
    private Buffer buffer;
    public byte[] load(String name) {
        return buffer.read(name);
    }
}
""",
    "src/main/java/acme/FastLoader.java": """
package acme;

public class FastLoader extends Loader {
    public byte[] load(String name) {
        return super.load(name);
    }
}
""",
    "src/main/java/acme/util/Buffer.java": """
package acme.util;

public class Buffer {
    public byte[] read(String name) { return new byte[0]; }
}
""",
    "src/main/java/acme/Report.java": """
package acme;

public class Report {
    private Loader loader;
    public String render() { return loader.toString(); }
}
""",
    "src/test/java/acme/LoaderTest.java": """
package acme;

import org.junit.Test;

public class LoaderTest {
    @Test
    public void loadsARecord() {
        Loader loader = new Loader();
        assertNotNull(loader.load("a"));
    }
}
""",
}


@pytest.fixture
def base_sources():
    return dict(BASE)


@pytest.fixture
def cache_added():
    """A new file that three existing files adopt: Change Propagation Type-I."""
    after = dict(BASE)
    after["src/main/java/acme/Cache.java"] = """
package acme;

public class Cache {
    public byte[] get(String key) { return null; }
}
"""
    after["src/main/java/acme/Loader.java"] = """
package acme;

import acme.util.Buffer;

public class Loader {
    private Buffer buffer;
    private Cache cache;
    public byte[] load(String name) { return cache.get(name); }
}
"""
    after["src/main/java/acme/FastLoader.java"] = """
package acme;

public class FastLoader extends Loader {
    private Cache cache;
    public byte[] load(String name) { return cache.get(name); }
}
"""
    after["src/main/java/acme/Report.java"] = """
package acme;

public class Report {
    private Loader loader;
    private Cache cache;
    public String render() { return cache.toString(); }
}
"""
    return after


@pytest.fixture
def single_file_edit():
    """One file, one line: localized."""
    after = dict(BASE)
    after["src/main/java/acme/util/Buffer.java"] = """
package acme.util;

public class Buffer {
    public byte[] read(String name) {
        if (name == null) { return new byte[0]; }
        return new byte[0];
    }
}
"""
    return after


@pytest.fixture
def rewired():
    """Loader drops Buffer and points at a sibling instead: Type-II."""
    after = dict(BASE)
    after["src/main/java/acme/Loader.java"] = """
package acme;

public class Loader {
    private Report report;
    public byte[] load(String name) { return report.render().getBytes(); }
}
"""
    after["src/main/java/acme/Report.java"] = """
package acme;

public class Report {
    public String render() { return "x"; }
}
"""
    return after
