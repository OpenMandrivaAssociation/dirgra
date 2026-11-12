Name:		dirgra
Version:	0.3
Release:	1
Summary:	Directed graph used by JRuby
Group:		Development/Java
License:	EPL-1.0
URL:		https://github.com/jruby/dirgra
# Tag 0.3. Eight Java sources. JRuby 9.4.14 compiles against this
# artifact. Upstream tests are Ruby specs. This package compiles with
# javac and checks DirectedGraph.addEdge.
Source0:	dirgra-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
org.jruby:dirgra %{version}. DirectedGraph.addEdge records a source
and a destination, and size returns the number of vertices. The
sources are compiled with javac.

%prep
%autosetup -n dirgra-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src -name '*.java' | sort > sources.list
test "$(wc -l < sources.list)" -eq 8

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes
javac --release 8 -Xlint:-options -encoding UTF-8 -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 10
javap -v -classpath classes org.jruby.dirgra.DirectedGraph | grep -F -q 'major version: 52'
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.jruby.dirgra' > manifest.mf
jar cfm dirgra.jar manifest.mf -C classes .
jar i dirgra.jar
jar tf dirgra.jar | grep -F -q 'org/jruby/dirgra/DirectedGraph.class'
desc=$(jar --describe-module --file dirgra.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -q 'org.jruby.dirgra'

cat > dirgra.pom << 'END'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jruby</groupId>
  <artifactId>dirgra</artifactId>
  <version>0.3</version>
  <name>dirgra</name>
  <description>Simple directed graph.</description>
  <url>https://github.com/jruby/dirgra</url>
  <licenses>
    <license>
      <name>EPL-1.0</name>
      <url>https://www.eclipse.org/legal/epl-v10.html</url>
    </license>
  </licenses>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact dirgra.pom:dirgra.jar \
	--file-name dirgra \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jruby/dirgra.sysjar"
test -s "$idx"
grep -F -q '"version": "0.3"' "$idx"
grep -F -q '"artifactId": "dirgra"' "$idx"
test -s %{buildroot}%{_javadir}/dirgra.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/dirgra.jar
test -s "$JAR"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.jruby.dirgra.DirectedGraph;
import org.jruby.dirgra.ExplicitVertexID;

public class Smoke {
    static final class Node implements ExplicitVertexID {
        private final int id;

        Node(int id) {
            this.id = id;
        }

        public int getID() {
            return id;
        }
    }

    public static void main(String[] args) {
        DirectedGraph<Node> graph = new DirectedGraph<Node>();
        graph.addEdge(new Node(1), new Node(2), "uses");
        int size = graph.size();
        if (size != 2) {
            throw new AssertionError(size);
        }
        System.out.println("dirgra_ok " + size);
    }
}
EOF
javac --release 8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'dirgra_ok 2' check/out.txt

%files -f .mfiles
%doc README.md
%license LICENSE.txt
