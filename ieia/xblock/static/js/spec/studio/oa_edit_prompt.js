import EditPromptsView from 'studio/oa_edit_prompts';
import { Prompt } from 'studio/oa_container_item';

/**
Tests for ieia prompt editing view.
**/

describe("ieia.EditPromptViews", function() {

    // Use a stub notifier implementation that simply stores
    // the notifications it receives.
    var notifier = null;
    var StubNotifier = function() {
        this.notifications = [];
        this.notificationFired = function(name, data) {
            this.notifications.push({
                name: name,
                data: data
            });
        };
    };

    var view = null;

    beforeEach(function() {
        // Load the DOM fixture
        loadFixtures('oa_edit.html');

        // Create the view
        var element = $("#oa_prompts_editor_wrapper").get(0);
        notifier = new StubNotifier();
        view = new EditPromptsView(element, notifier);
    });

    afterEach(function() {
        Prompt.prototype.tinyMCEEnabled = undefined;
    });

    it("reads prompts from the editor", function() {
        // This assumes a particular structure of the DOM,
        // which is set by the HTML fixture.
        var prompts = view.promptsDefinition();
        expect(prompts.length).toEqual(2);

        expect(prompts[0]).toEqual({
            "description": "How much do you like waffles?"
        });
    });

    it("creates new prompts", function() {
        // Delete all existing prompts
        // Then add new prompts (created from a client-side template)
        $.each(view.getAllPrompts(), function() { view.removePrompt(this); });
        view.addPrompt();
        view.addPrompt();
        view.addPrompt();

        var prompts = view.promptsDefinition();
        expect(prompts.length).toEqual(3);

        expect(prompts[0]).toEqual({
            description: ""
        });

        expect(prompts[1]).toEqual({
            description: ""
        });
    });

    it("creates new html prompts", function() {
        const oldTinyMCE = window.tinyMCE;
        window.tinyMCE = () => ({});
        Prompt.prototype.tinyMCEEnabled = true;
        spyOn(Prompt.prototype, 'attachWysiwygToPrompt');
        spyOn(Prompt.prototype, 'addHandler');

        view.addPrompt();
        expect(Prompt.prototype.attachWysiwygToPrompt).toHaveBeenCalled();
        expect(Prompt.prototype.addHandler).toHaveBeenCalled();
        window.tinyMCE = oldTinyMCE;
    });
});

describe("ieia.EditPromptViews after release", function() {

    // Use a stub notifier implementation that simply stores
    // the notifications it receives.
    var notifier = null;
    var StubNotifier = function() {
        this.notifications = [];
        this.notificationFired = function(name, data) {
            this.notifications.push({
                name: name,
                data: data
            });
        };
    };

    var view = null;

    beforeEach(function() {
        // Load the DOM fixture
        loadFixtures('oa_edit.html');
        $("#ieia-editor").attr('data-is-released', 'true');

        // Create the view
        var element = $("#oa_prompts_editor_wrapper").get(0);
        notifier = new StubNotifier();
        view = new EditPromptsView(element, notifier);
    });

    it("does not allow adding prompts", function() {
        view.addPrompt(); // call method
        $(view.promptsContainer.addButtonElement).click(); // click on button

        var prompts = view.promptsDefinition();
        expect(prompts.length).toEqual(2);
    });

    it("does not allow removing prompts", function() {
        view.removePrompt(view.getAllPrompts()[0]); // call method
        $("." + view.promptsContainer.removeButtonClass, view.element).click(); // click on buttons

        var prompts = view.promptsDefinition();
        expect(prompts.length).toEqual(2);
    });
});
