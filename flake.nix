{
  description = "yt-dlp-mirainime development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages (p: [p.yt-dlp]))
            yt-dlp
            mitmproxy
          ];

          shellHook = ''
            echo "Development environment for yt-dlp plugin active!"
            echo "Python: $(python3 --version)"
            echo "yt-dlp: $(yt-dlp --version)"
            echo "mitmproxy: $(mitmproxy --version)"
          '';
        };
      }
    );
}
# vi: nowrap
