class Eznet < Formula
  desc "Comprehensive network testing CLI tool"
  homepage "https://github.com/batr7434/eznet"
  url "https://github.com/batr7434/eznet/archive/v0.2.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    system "python3.12", "-m", "pip", "install", "--target=#{libexec}", "."
    
    # Create wrapper script
    (bin/"eznet").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{libexec}:$PYTHONPATH"
      python3.12 -m eznet.cli "$@"
    EOS
  end

  test do
    system "#{bin}/eznet", "--help"
  end
end