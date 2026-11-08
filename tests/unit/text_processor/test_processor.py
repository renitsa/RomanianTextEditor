"""
Unit tests for TextProcessor, the @register_task decorator and DiacriticAdder.
"""
import unittest
from unittest.mock import Mock, patch

from src.config.app_config import get_app_config
from src.text_processor import TextProcessor, DiacriticAdder, TASK_REGISTRY, register_task


def make_processor(processor_class=TextProcessor, **kwargs):
    """Create a processor whose Ollama service is a mock."""
    service = Mock()
    with patch('src.services.get_ollama_service', return_value=service):
        processor = processor_class("test_model", **kwargs)
    return processor, service


class TestRegisterTask(unittest.TestCase):
    """Test the @register_task decorator."""

    def tearDown(self):
        """Remove tasks registered by the tests."""
        TASK_REGISTRY.pop("sample_task", None)

    def test_registers_class_and_sets_task_name(self):
        """The decorator stores the class and sets TASK_NAME."""
        @register_task("sample_task")
        class SampleTask(TextProcessor):
            pass

        self.assertIs(TASK_REGISTRY["sample_task"], SampleTask)
        self.assertEqual(SampleTask.TASK_NAME, "sample_task")

    def test_duplicate_name_for_different_class_raises(self):
        """Registering two different classes under one name is an error."""
        @register_task("sample_task")
        class First(TextProcessor):
            pass

        with self.assertRaises(ValueError) as context:
            @register_task("sample_task")
            class Second(TextProcessor):
                pass

        self.assertIn("already registered", str(context.exception))

    def test_registering_same_class_again_is_allowed(self):
        """Re-registering the same class (e.g. on module reload) is harmless."""
        class Sample(TextProcessor):
            pass

        register_task("sample_task")(Sample)
        register_task("sample_task")(Sample)

        self.assertIs(TASK_REGISTRY["sample_task"], Sample)

    def test_invalid_names_raise(self):
        """Task names must be non-empty and lower-case."""
        for bad_name in ("", "Sample_Task"):
            with self.subTest(name=bad_name):
                with self.assertRaises(ValueError):
                    register_task(bad_name)

    def test_builtin_tasks_registered(self):
        """The diacritics task ships with a registered class."""
        self.assertIs(TASK_REGISTRY["diacritics"], DiacriticAdder)


class TestTextProcessor(unittest.TestCase):
    """Test the template method and configuration handling."""

    def test_prompt_comes_from_task_config(self):
        """The prompt is read from the task's config entry."""
        processor, _ = make_processor(task_name="summarize")

        self.assertEqual(
            processor.prompt, get_app_config().actions_config.SUMMARIZE.PROMPT
        )

    def test_process_text_sends_prompt_and_text(self):
        """The LLM receives the configured prompt followed by the text."""
        processor, service = make_processor(task_name="edit")
        service.generate_response.return_value = "edited"

        result = processor.process_text("some text")

        self.assertEqual(result, "edited")
        service.generate_response.assert_called_once_with(
            "test_model", f"{processor.prompt} some text"
        )

    def test_custom_prompt_overrides_configured_prompt(self):
        """An explicit prompt takes precedence over the config."""
        processor, service = make_processor(task_name="edit")
        service.generate_response.return_value = "ok"

        processor.process_text("text", custom_prompt="Do this:")

        service.generate_response.assert_called_once_with("test_model", "Do this: text")

    def test_failed_llm_call_returns_none_without_postprocess(self):
        """A None response from the LLM is returned as None, postprocess is skipped."""
        class Spy(TextProcessor):
            called = False

            def postprocess(self, text):
                Spy.called = True
                return text

        processor, service = make_processor(Spy, task_name="edit")
        service.generate_response.return_value = None

        self.assertIsNone(processor.process_text("text"))
        self.assertFalse(Spy.called)

    def test_hooks_wrap_the_llm_call(self):
        """preprocess runs before the LLM call and postprocess after it."""
        class Shouting(TextProcessor):
            def preprocess(self, text):
                return text.upper()

            def postprocess(self, text):
                return text + "!"

        processor, service = make_processor(Shouting, task_name="edit")
        service.generate_response.return_value = "answer"

        result = processor.process_text("question")

        self.assertEqual(result, "answer!")
        service.generate_response.assert_called_once_with(
            "test_model", f"{processor.prompt} QUESTION"
        )

    def test_missing_task_name_raises(self):
        """The base class needs a task name to find its config."""
        with self.assertRaises(ValueError) as context:
            make_processor()

        self.assertIn("task name", str(context.exception))

    def test_unknown_config_entry_raises(self):
        """A task without an entry in the config is rejected with the valid options."""
        with self.assertRaises(ValueError) as context:
            make_processor(task_name="no_such_task")

        self.assertIn("NO_SUCH_TASK", str(context.exception))
        self.assertIn("DIACRITICS", str(context.exception))


class TestDiacriticAdder(unittest.TestCase):
    """Test the diacritics task with custom post-processing."""

    def test_postprocess_replaces_cedilla_with_comma_below(self):
        """Legacy cedilla letters become the correct comma-below letters."""
        processor, _ = make_processor(DiacriticAdder)

        self.assertEqual(processor.postprocess("şţ ŞŢ"), "șț ȘȚ")

    def test_postprocess_keeps_other_text_unchanged(self):
        """Text without cedilla letters is not modified."""
        processor, _ = make_processor(DiacriticAdder)
        text = "Fata frumoasă și înțeleaptă"

        self.assertEqual(processor.postprocess(text), text)

    def test_process_text_applies_postprocess(self):
        """The LLM answer goes through the cedilla fix."""
        processor, service = make_processor(DiacriticAdder)
        service.generate_response.return_value = "ţara şi"

        self.assertEqual(processor.process_text("tara si"), "țara și")


if __name__ == "__main__":
    unittest.main()
