import json
from enum import Enum
from subprocess import check_output
from time import sleep
from typing import Optional

from serial import Serial


class PortInfo(object):
    def __init__(self, rawinfo: dict):
        from serial.tools.list_ports import grep

        self._rawinfo = rawinfo

        self.__board: Optional[str] = None
        self.__fqbn: Optional[str] = None
        self.__port: Optional[str] = None
        self.__serial_number: Optional[str] = None

        boardinfo_list: Optional[list[dict]] = (
            rawinfo.get("matching_boards")
            or rawinfo.get("matchingboards")
            or rawinfo.get("boards")
        )

        portinfo: Optional[dict] = rawinfo.get("port") or rawinfo

        if not boardinfo_list or portinfo is None:
            raise ValueError(f"Invalid Arduino board info: {rawinfo}")

        boardinfo: dict = boardinfo_list[0]

        self.__board = boardinfo.get("name")
        self.__fqbn = boardinfo.get("fqbn")
        self.__port = portinfo.get("address")

        properties = portinfo.get("properties") or {}
        self.__serial_number = (
            rawinfo.get("serial_number")
            or properties.get("serialNumber")
            or properties.get("serial_number")
        )

        if self.__serial_number is None and self.__port is not None:
            ports = list(grep(self.__port))
            if len(ports) > 0:
                self.__serial_number = ports[0].serial_number

    @property
    def board(self) -> Optional[str]:
        return self.__board

    @property
    def fqbn(self) -> Optional[str]:
        return self.__fqbn

    @property
    def port(self) -> Optional[str]:
        return self.__port

    @property
    def serial_number(self) -> Optional[str]:
        return self.__serial_number

    def __repr__(self) -> str:
        return f"{self.board} at {self.port}"

    def detail(self) -> dict:
        if self.port is None:
            raise ValueError("Port is not available")

        output = check_output(
            [
                "arduino-cli",
                "monitor",
                "-p",
                self.port,
                "--describe",
                "--format",
                "json",
            ],
            text=True,
        )
        return json.loads(output)

    def to_dict(self) -> dict:
        return {
            "board": self.board,
            "port": self.port,
            "fqbn": self.fqbn,
            "serial_number": self.serial_number,
        }


def check_connected_board_info() -> list[PortInfo]:
    output = check_output(
        [
            "arduino-cli",
            "board",
            "list",
            "--format",
            "json",
        ],
        text=True,
    )

    detected = json.loads(output)

    if isinstance(detected, dict):
        detected_ports = detected.get("detected_ports", [])
    else:
        detected_ports = detected

    boards_raw_info = [
        d for d in detected_ports
        if (
            d.get("matching_boards")
            or d.get("matchingboards")
            or d.get("boards")
        )
    ]

    return list(map(PortInfo, boards_raw_info))
