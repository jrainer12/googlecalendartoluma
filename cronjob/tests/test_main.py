#!/usr/bin/env python3
"""
Tests for main function.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from icalendar import Calendar


class TestMain:
    """Tests for main function."""
    
    def test_main_success(self):
        """Test successful main execution."""
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create future events
            future_time = datetime.now(timezone.utc) + timedelta(days=1)
            events = [
                {
                    'summary': 'Test Event 1',
                    'description': 'Test Description',
                    'location': 'Test Location',
                    'start_utc': future_time,
                    'end_utc': future_time + timedelta(hours=1)
                },
                {
                    'summary': 'Test Event 2',
                    'description': 'Test Description 2',
                    'location': 'Test Location 2',
                    'start_utc': future_time + timedelta(hours=2),
                    'end_utc': future_time + timedelta(hours=3)
                }
            ]
            
            # Patch OUT_DIR before importing main
            with patch.dict('sys.modules', {}):
                import main
                with patch.object(main, 'OUT_DIR', tmpdir):
                    with patch.object(main, 'embed_to_ics', return_value=('https://example.com/calendar.ics', 'UTC')):
                        with patch.object(main, 'load_ics', return_value=Calendar()):
                            with patch.object(main, 'next_upcoming_events', return_value=events):
                                main.main()
                                
                                # Check that files were created
                                files = os.listdir(tmpdir)
                                assert len(files) == 2
                                assert any('test-event-1' in f for f in files)
                                assert any('test-event-2' in f for f in files)
                                
                                # Check that files contain valid JSON
                                for filename in files:
                                    filepath = os.path.join(tmpdir, filename)
                                    with open(filepath, 'r', encoding='utf-8') as f:
                                        payload = json.load(f)
                                        assert 'name' in payload
                                        assert 'start_at' in payload
                                        assert 'calendar_api_id' in payload
    
    def test_main_no_events(self):
        """Test main when no upcoming events are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import main
            with patch.object(main, 'OUT_DIR', tmpdir):
                with patch.object(main, 'embed_to_ics', return_value=('https://example.com/calendar.ics', 'UTC')):
                    with patch.object(main, 'load_ics', return_value=Calendar()):
                        with patch.object(main, 'next_upcoming_events', return_value=[]):
                            main.main()
                            
                            # No files should be created
                            files = os.listdir(tmpdir)
                            assert len(files) == 0
    
    def test_main_handles_duplicate_filenames(self):
        """Test main handles duplicate filenames correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create events with same summary (will create duplicate filenames)
            future_time = datetime.now(timezone.utc) + timedelta(days=1)
            events = [
                {
                    'summary': 'Test Event',
                    'description': 'Description 1',
                    'location': 'Location 1',
                    'start_utc': future_time,
                    'end_utc': future_time + timedelta(hours=1)
                },
                {
                    'summary': 'Test Event',
                    'description': 'Description 2',
                    'location': 'Location 2',
                    'start_utc': future_time + timedelta(hours=2),
                    'end_utc': future_time + timedelta(hours=3)
                }
            ]
            
            import main
            with patch.object(main, 'OUT_DIR', tmpdir):
                with patch.object(main, 'embed_to_ics', return_value=('https://example.com/calendar.ics', 'UTC')):
                    with patch.object(main, 'load_ics', return_value=Calendar()):
                        with patch.object(main, 'next_upcoming_events', return_value=events):
                            main.main()
                            
                            # Check that files were created with different names
                            files = sorted(os.listdir(tmpdir))
                            assert len(files) == 2
                            # First file should be test-event.json, second should be test-event-2.json
                            assert 'test-event.json' in files[0] or 'test-event.json' in files[1]
                            assert any('test-event-2.json' in f for f in files) or any('test-event-1.json' in f for f in files)
    
    def test_main_handles_exception(self):
        """Test main handles exceptions correctly."""
        import sys
        import main
        with patch.object(main, 'embed_to_ics', side_effect=Exception("Test error")):
            with patch('sys.exit') as mock_exit:
                main.main()
                mock_exit.assert_called_once_with(1)
