/**
Interface for Message banner.

Args:
    element (DOM element): The DOM element representing the XBlock.
    server (ieia.Server): The interface to the XBlock server.
    baseView (ieia.BaseView): Container view.

Returns:
    ieia.ResponseView
* */

export class MessageView {
  constructor(element, server, baseView) {
    this.element = element;
    this.server = server;
    this.baseView = baseView;
  }

  /**
    Loads the message view.
    * */
  load() {
    const view = this;
    const { baseView } = this;
    this.server.render('message').done(
      (html) => {
        // Load the HTML
        $('.openassessment__message', view.element).replaceWith(html);
        view.server.renderLatex($('.openassessment__message', view.element));
      },
    ).fail((errMsg) => {
      baseView.showLoadError('message', errMsg);
    });
  }
}

export default MessageView;
