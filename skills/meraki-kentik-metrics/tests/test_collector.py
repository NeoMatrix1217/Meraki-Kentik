import os
import tempfile
import unittest
from collector import build_metrics, escape_tag, field_value, line, load_config, load_dotenv_file, mock_payloads


class CollectorTests(unittest.TestCase):
    def test_mock_metrics_include_dashboard_measurements(self):
        metrics = build_metrics(mock_payloads(), "org-123", 1700000000000000000)
        self.assertEqual(len(metrics), 7)
        self.assertTrue(any(x.startswith("meraki_device_status,") for x in metrics))
        self.assertTrue(any(x.startswith("meraki_uplink_quality,") for x in metrics))
        self.assertTrue(any(x.startswith("meraki_uplink_status,") for x in metrics))
        self.assertTrue(any(x.startswith("meraki_wireless_connection,") for x in metrics))
        self.assertTrue(any(x.startswith("meraki_wireless_client,") for x in metrics))
        self.assertTrue(any(x.startswith("meraki_wireless_access_point,") for x in metrics))
        ap = next(x for x in metrics if x.startswith("meraki_wireless_access_point,"))
        self.assertIn("ap_ip=10.0.0.2", ap)
        self.assertIn("ap_mac=aa:bb:cc:dd:ee:02", ap)
        self.assertIn("bssid=aa:bb:cc:dd:ee:03", ap)
        self.assertIn("ssid=Corp-WiFi", ap)
        self.assertIn("radio_type=5", ap)
        self.assertIn("channel=36i", ap)
        self.assertIn("current_endpoint_count=7i", ap)
        self.assertIn("bandwidth_utilization_kbps=2450.0", ap)
        self.assertIn("channel_utilization_percent=42.5", ap)
        wireless = next(x for x in metrics if x.startswith("meraki_wireless_client,"))
        self.assertIn("client_name=Lab\\ Laptop", wireless)
        self.assertIn("connected=true", wireless)
        self.assertIn("data_rate_kbps=12000.0", wireless)
        self.assertIn("data_rate_bps=12000000.0", wireless)
        self.assertIn("throughput_kbps=12000.0", wireless)
        self.assertIn("signal_strength_dbm=-58.0", wireless)
        self.assertIn("connected_at=\"2026-10-14T12:00:00Z\"", wireless)
        self.assertIn("transmitted_mb=120.5625", wireless)
        self.assertIn("loss_percent=0.5", "\n".join(metrics))
        self.assertIn("latency_ms=23.4", "\n".join(metrics))

    def test_escaping(self):
        self.assertEqual(escape_tag("a b,c=d"), "a\\ b\\,c\\=d")
        self.assertEqual(field_value('a"b'), '"a\\"b"')

    def test_integer_and_float_fields(self):
        result = line("m", {"host": "x"}, {"count": 2, "ratio": 1.5})
        self.assertIn("count=2i", result)
        self.assertIn("ratio=1.5", result)

    def test_client_timespan_defaults_to_one_day_and_is_configurable(self):
        default_config = load_config({})
        self.assertEqual(default_config.client_timespan_seconds, 86400)
        custom_config = load_config({"MERAKI_CLIENT_TIMESPAN": "3600"})
        self.assertEqual(custom_config.client_timespan_seconds, 3600)

    def test_dotenv_loader_does_not_override_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            dotenv = os.path.join(directory, ".env")
            with open(dotenv, "w", encoding="utf-8") as handle:
                handle.write("TEST_MERAKI_KEY=example\n")
            old = os.environ.pop("TEST_MERAKI_KEY", None)
            try:
                load_dotenv_file(dotenv)
                self.assertEqual(os.environ["TEST_MERAKI_KEY"], "example")
            finally:
                os.environ.pop("TEST_MERAKI_KEY", None)
                if old is not None:
                    os.environ["TEST_MERAKI_KEY"] = old


if __name__ == "__main__":
    unittest.main()
