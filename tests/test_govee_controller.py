#!/usr/bin/env python3
"""Tests for Govee controller functionality."""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
import json
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from govee_controller import GoveeController


class TestGoveeController(unittest.TestCase):
    """Test GoveeController functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.device_id = "AA:BB:CC:DD:EE:FF:11:22"
        self.device_model = "H6159"
        
    def test_initialization(self):
        """Test GoveeController initialization."""
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        self.assertEqual(controller.api_key, self.api_key)
        self.assertEqual(controller.device_id, self.device_id)
        self.assertEqual(controller.device_model, self.device_model)
        
    @patch('govee_controller.requests.put')
    def test_set_color_success(self, mock_put):
        """Test setting color successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        controller.set_color(255, 128, 0)  # Method doesn't return value currently
        
        mock_put.assert_called_once()
        
        # Check the API call parameters
        call_args = mock_put.call_args
        self.assertIn('Govee-API-Key', call_args[1]['headers'])
        self.assertEqual(call_args[1]['headers']['Govee-API-Key'], self.api_key)
        
        # Check the payload
        payload = call_args[1]['json']
        self.assertEqual(payload['device'], self.device_id)
        self.assertEqual(payload['model'], self.device_model)
        self.assertEqual(payload['cmd']['name'], 'color')
        self.assertEqual(payload['cmd']['value'], {'r': 255, 'g': 128, 'b': 0})
        
    @patch('govee_controller.requests.put')
    def test_set_color_failure(self, mock_put):
        """Test setting color with API failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        mock_put.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        controller.set_color(255, 128, 0)  # Should not raise exception
        
        mock_put.assert_called_once()
        
    @patch('govee_controller.requests.put')
    def test_set_brightness_success(self, mock_put):
        """Test setting brightness successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        controller.set_brightness(75)  # Method doesn't return value currently
        
        mock_put.assert_called_once()
        
        # Check the payload
        call_args = mock_put.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['cmd']['name'], 'brightness')
        self.assertEqual(payload['cmd']['value'], 75)
        
    @patch('govee_controller.requests.get')
    def test_is_on_true(self, mock_get):
        """Test checking if device is on when it's on."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "device": self.device_id,
                "model": self.device_model,
                "status": {
                    "powerState": "on"
                }
            }
        }
        mock_get.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        result = controller.is_on()
        
        self.assertTrue(result)
        
    @patch('govee_controller.requests.get')
    def test_is_on_false(self, mock_get):
        """Test checking if device is on when it's off."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "device": self.device_id,
                "model": self.device_model,
                "status": {
                    "powerState": "off"
                }
            }
        }
        mock_get.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        result = controller.is_on()
        
        self.assertFalse(result)
        
    @patch('govee_controller.requests.get')
    def test_is_on_api_error(self, mock_get):
        """Test checking device state with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        mock_get.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        result = controller.is_on()
        
        self.assertFalse(result)
        
    @patch('govee_controller.requests.put')
    def test_set_power_on(self, mock_put):
        """Test turning device on."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        controller.set_power(True)  # Method doesn't return value currently
        
        mock_put.assert_called_once()
        
        # Check the payload
        call_args = mock_put.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['cmd']['name'], 'turn')
        self.assertEqual(payload['cmd']['value'], True)
        
    @patch('govee_controller.requests.put')
    def test_set_power_off(self, mock_put):
        """Test turning device off."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        controller = GoveeController(self.api_key, self.device_id, self.device_model)
        controller.set_power(False)  # Method doesn't return value currently
        
        mock_put.assert_called_once()
        
        # Check the payload
        call_args = mock_put.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['cmd']['name'], 'turn')
        self.assertEqual(payload['cmd']['value'], False)


if __name__ == '__main__':
    unittest.main()
