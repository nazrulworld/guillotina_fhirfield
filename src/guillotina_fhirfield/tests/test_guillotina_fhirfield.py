#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `guillotina_fhirfield` package."""

import pytest
from click.testing import CliRunner

import guillotina_fhirfield
from guillotina_fhirfield import cli


async def test_content(dummy_request, dummy_guillotina):  # noqa: E999
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'guillotina_fhirfield.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
