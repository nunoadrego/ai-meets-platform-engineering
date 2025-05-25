package main

import (
	"context"
	"fmt"
	"io"
	"net/http"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	// Create a new MCP server
	s := server.NewMCPServer(
		"Platform MCP",
		"0.1.0",
		server.WithToolCapabilities(false),
	)

	// Tools
	listAppsTool := mcp.NewTool("list_apps",
		mcp.WithDescription("List all apps in the platform"),
	)
	getAppDetailsTool := mcp.NewTool("get_app_details",
		mcp.WithDescription("Get details of a specific app in the platform"),
		mcp.WithNumber("app_id",
			mcp.Required(),
			mcp.Description("Application ID"),
		),
	)

	// Tool handlers
	s.AddTool(listAppsTool, listAppsHandler)
	s.AddTool(getAppDetailsTool, getAppDetailsHandler)

	// Start the stdio server
	if err := server.ServeStdio(s); err != nil {
		fmt.Printf("Server error: %v\n", err)
	}
}

func listAppsHandler(ctx context.Context, _ mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	response, err := http.Get("http://localhost:8080/apps")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	return mcp.NewToolResultText(string(body)), nil
}

func getAppDetailsHandler(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	appID, err := request.RequireInt("app_id")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	response, err := http.Get(fmt.Sprintf("http://localhost:8080/apps/%d", appID))
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	defer response.Body.Close()
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}

	return mcp.NewToolResultText(string(body)), nil
}
