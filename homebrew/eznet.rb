class Eznet < Formula
  desc "Comprehensive network testing CLI tool with port scanning and SSL certificate analysis"
  homepage "https://github.com/batr7434/eznet"
  url "https://github.com/batr7434/eznet/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "Apache-2.0"
  head "https://github.com/batr7434/eznet.git", branch: "main"

  depends_on "python@3.12"

  resource "click" do
    url "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf2b5c0/click-8.3.0.tar.gz"
    sha256 "7682dc8afb30297001674575ea00d1814d808d6a36af415a82bd481d37ba7b8e"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/87/67/a37f6214d0e9fe57f6c54b3b2619e827f367fcfd6fe4a5f7dafd51db6cbc/rich-14.2.0.tar.gz"
    sha256 "fb9d6c0a0f643c99eed3875b5377a184132ba9be4d61516a55273d3554d75a39"
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/78/82/08f8c936781f67d9e6b9eeb8a0c8b4e406136ea4c3d1f89a5db71d42e0e7/httpx-0.28.1.tar.gz"
    sha256 "75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc"
  end

  resource "aiodns" do
    url "https://files.pythonhosted.org/packages/e7/84/41a6a2765abc124563f5380e76b9b24118977729e25a84ca8fbf2af47e7f5/aiodns-3.5.0.tar.gz"
    sha256 "c5fd5a62a202547d7c31b6f0f6c8e72b61bf2c2ffd6dbdf31a2c6fcfab52b5c5"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "EZNet", shell_output("#{bin}/eznet --help")
    system bin/"eznet", "--version"
  end
end